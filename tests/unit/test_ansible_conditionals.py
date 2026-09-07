import unittest
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from ansible.errors import AnsibleBrokenConditionalError
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar, trust_as_template
from jinja2 import Environment, nodes


REPO_ROOT = Path(__file__).resolve().parents[2]
JINJA_ENVIRONMENT = Environment()
CONDITIONAL_FIELDS = ("when", "until", "changed_when", "failed_when")


def yaml_patterns(*paths):
    return tuple(
        f"{path}/*.{extension}" for path in paths for extension in ("yml", "yaml")
    )


ANSIBLE_FILE_PATTERNS = yaml_patterns(
    "playbooks/**",
    "extra_playbooks/**",
    "roles/**/handlers/**",
    "roles/**/meta/**",
    "roles/**/molecule/**",
    "roles/**/tasks/**",
    "tests/cloud_playbooks/**",
    "tests/testcases/**",
    "scripts",
    "contrib/**",
    "test-infra/**",
)
DEFAULT_FILE_PATTERNS = yaml_patterns("roles/**/defaults/**")

NON_BOOLEAN_ATTRIBUTES = frozenset(
    "files rc resources results stderr stderr_lines stdout stdout_lines".split()
)


def matching_paths(patterns):
    return sorted({path for pattern in patterns for path in REPO_ROOT.glob(pattern)})


def walk_mappings(value):
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_mappings(child)


def normalize_conditions(value):
    return value if isinstance(value, list) else [value]


def load_non_boolean_defaults(loader):
    types = defaultdict(set)
    for path in matching_paths(DEFAULT_FILE_PATTERNS):
        data = loader.load_from_file(str(path), trusted_as_template=True)
        for name, value in data.items() if isinstance(data, Mapping) else ():
            if isinstance(name, str):
                templated = isinstance(value, str) and ("{{" in value or "{%" in value)
                types[name].add(not isinstance(value, bool) and not templated)
    return {name for name, values in types.items() if values == {True}}


def is_non_boolean_expression(node, registered_variables, non_boolean_defaults):
    if isinstance(node, (nodes.Compare, nodes.Not, nodes.Test)):
        return False
    if isinstance(node, nodes.Const):
        return not isinstance(node.value, bool)
    if isinstance(node, (nodes.Dict, nodes.List, nodes.Tuple)):
        return True
    if isinstance(node, nodes.Name):
        return node.name in registered_variables or node.name in non_boolean_defaults
    if isinstance(node, nodes.Getitem):
        name = node.node.name if isinstance(node.node, nodes.Name) else None
        return (
            name == "groups"
            or name in registered_variables
            and isinstance(node.arg, nodes.Const)
            and node.arg.value in NON_BOOLEAN_ATTRIBUTES
        )
    if isinstance(node, nodes.Getattr):
        return (
            isinstance(node.node, nodes.Name)
            and node.node.name in registered_variables
            and node.attr in NON_BOOLEAN_ATTRIBUTES
        )
    return False


def is_non_boolean_condition(condition, registered_variables, non_boolean_defaults):
    if isinstance(condition, bool):
        return False
    if not isinstance(condition, str):
        return True
    expression_text = condition.strip()
    if expression_text.startswith("{{") and expression_text.endswith("}}"):
        expression_text = expression_text[2:-2].strip()
    parsed = JINJA_ENVIRONMENT.parse("{{ " + expression_text + " }}")
    return is_non_boolean_expression(
        parsed.body[0].nodes[0],
        registered_variables,
        non_boolean_defaults,
    )


def scan_non_boolean_conditionals(loader):
    non_boolean_defaults = load_non_boolean_defaults(loader)
    findings = []

    for path in matching_paths(ANSIBLE_FILE_PATTERNS):
        data = loader.load_from_file(str(path), trusted_as_template=True)
        mappings = list(walk_mappings(data))
        registered_variables = {
            item["register"]
            for item in mappings
            if isinstance(item.get("register"), str)
        }

        for task in mappings:
            for field in CONDITIONAL_FIELDS:
                if field not in task:
                    continue
                for index, condition in enumerate(normalize_conditions(task[field])):
                    if is_non_boolean_condition(
                        condition,
                        registered_variables,
                        non_boolean_defaults,
                    ):
                        findings.append(
                            f"{path.relative_to(REPO_ROOT)}: "
                            f"{task.get('name', '<unnamed>')} "
                            f"[{field}[{index}]]: {condition}"
                        )
    return findings


class AnsibleConditionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()

    def test_repository_has_no_definite_non_boolean_conditionals(self):
        findings = scan_non_boolean_conditionals(self.loader)
        self.assertFalse(findings, "\n".join(findings))

    def evaluator_is_broken(self, condition, variables=None):
        if isinstance(condition, str):
            condition = trust_as_template(condition)
        try:
            result = Templar(
                loader=self.loader,
                variables=variables or {},
            ).evaluate_conditional(condition)
        except AnsibleBrokenConditionalError:
            return True
        self.assertIsInstance(result, bool)
        return False

    def test_scanner_rules_match_ansible(self):
        registered_variables = {"command_result"}
        non_boolean_defaults = {"string_option"}
        result = {"command_result": {"stdout": "value"}}
        groups = {"groups": {"workers": ["node"]}}
        cases = (
            (None, {}, True),
            (1, {}, True),
            (1.0, {}, True),
            ({}, {}, True),
            ([], {}, True),
            ([[]], {}, True),
            (True, {}, False),
            (False, {}, False),
            ("command_result", result, True),
            ("string_option", {"string_option": "value"}, True),
            ("command_result.stdout", result, True),
            ("command_result['stdout']", result, True),
            ("groups['workers']", groups, True),
            ("'value'", {}, True),
            ("[]", {}, True),
            ("{}", {}, True),
            ("('a', 'b')", {}, True),
            ("boolean_option", {"boolean_option": True}, False),
            ("not boolean_option", {"boolean_option": True}, False),
            ("option is defined", {}, False),
            ("command_result is failed", {"command_result": {"failed": True}}, False),
            ("'node' in groups['workers']", groups, False),
            ("command_result.stdout | length > 0", result, False),
            ("groups['workers'] | length > 0", groups, False),
            ("boolean_mapping.stdout", {"boolean_mapping": {"stdout": True}}, False),
        )
        self.assertEqual([], normalize_conditions([]))
        self.assertEqual([[]], normalize_conditions([[]]))
        for expression, variables, expected in cases:
            with self.subTest(expression=expression):
                self.assertEqual(
                    expected,
                    is_non_boolean_condition(
                        expression,
                        registered_variables,
                        non_boolean_defaults,
                    ),
                )
                self.assertEqual(
                    expected,
                    self.evaluator_is_broken(expression, variables),
                )

    def test_ansible_evaluator_expression_boundaries(self):
        old_registry = "registry_storage_class != none and registry_storage_class"
        new_registry = (
            "registry_storage_class is not none and registry_storage_class | length > 0"
        )
        result = {"command_result": {"stdout": "value"}}
        short_circuit = "boolean_option or command_result.stdout"
        iterator_sum = "(range(1, 3) | map('pow', 2)) + (range(1, 3) | map('pow', 3))"
        iterator_comparison = f"({iterator_sum}) == [1.0, 4.0, 1.0, 8.0]"
        cases = (
            ("values | length", {"values": [1, 2]}, True),
            (old_registry, {"registry_storage_class": None}, False),
            (old_registry, {"registry_storage_class": "fast"}, True),
            (short_circuit, {"boolean_option": True, **result}, False),
            (short_circuit, {"boolean_option": False, **result}, True),
            ("true or command_result.stdout", result, False),
            (new_registry, {"registry_storage_class": None}, False),
            (new_registry, {"registry_storage_class": ""}, False),
            (new_registry, {"registry_storage_class": "fast"}, False),
            (iterator_sum, {}, True),
            (iterator_comparison, {}, False),
        )
        for expression, variables, broken in cases:
            with self.subTest(expression=expression):
                self.assertEqual(
                    broken,
                    self.evaluator_is_broken(expression, variables),
                )
