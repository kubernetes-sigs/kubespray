import unittest
from collections.abc import Mapping
from pathlib import Path

from ansible.errors import AnsibleBrokenConditionalError
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar, trust_as_template


REPO_ROOT = Path(__file__).resolve().parents[2]


def walk_tasks(value):
    if isinstance(value, Mapping):
        if isinstance(value.get("name"), str):
            yield value
        for child in value.values():
            yield from walk_tasks(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_tasks(child)


def normalize_conditions(value):
    return value if isinstance(value, list) else [value]


class AnsibleConditionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()

    def load_task(self, path, name):
        data = self.loader.load_from_file(
            str(REPO_ROOT / path),
            trusted_as_template=True,
        )
        return next(task for task in walk_tasks(data) if task["name"] == name)

    def evaluate(self, condition, variables=None):
        if isinstance(condition, str):
            condition = trust_as_template(condition)
        return Templar(
            loader=self.loader,
            variables=variables or {},
        ).evaluate_conditional(condition)

    def assert_condition_results(
        self,
        path,
        task_name,
        field,
        variables,
        expected,
    ):
        conditions = normalize_conditions(self.load_task(path, task_name)[field])
        self.assertEqual(
            expected,
            [self.evaluate(condition, variables) for condition in conditions],
        )

    def test_registry_storage_conditions(self):
        path = "roles/kubernetes-apps/registry/tasks/main.yml"
        task_names = (
            "Registry | Create PVC manifests",
            "Registry | Apply PVC manifests",
        )
        cases = (
            (None, None, [False, False, True]),
            ("", "", [False, False, True]),
            ("fast", "10Gi", [True, True, True]),
        )

        for task_name in task_names:
            for storage_class, disk_size, expected in cases:
                with self.subTest(
                    task=task_name,
                    storage_class=storage_class,
                    disk_size=disk_size,
                ):
                    self.assert_condition_results(
                        path,
                        task_name,
                        "when",
                        {
                            "registry_storage_class": storage_class,
                            "registry_disk_size": disk_size,
                            "inventory_hostname": "control-plane-1",
                            "groups": {"kube_control_plane": ["control-plane-1"]},
                        },
                        expected,
                    )

    def test_recovery_group_conditions(self):
        cases = (
            (
                "roles/recover_control_plane/control-plane/tasks/main.yml",
                "broken_kube_control_plane",
                (
                    "Wait for apiserver",
                    "Delete broken kube_control_plane nodes from cluster",
                    "Fail if unable to delete broken kube_control_plane nodes from cluster",
                ),
            ),
            (
                "roles/recover_control_plane/etcd/tasks/main.yml",
                "broken_etcd",
                (
                    "Get etcd endpoint health",
                    "Set healthy fact",
                    "Set has_quorum fact",
                    "Recover lost etcd quorum",
                    "Remove etcd data dir",
                    "Delete old certificates",
                    "Fail if unable to delete old certificates",
                    "Get etcd cluster members",
                    "Remove broken cluster members",
                ),
            ),
        )

        for path, group_name, task_names in cases:
            for task_name in task_names:
                condition = normalize_conditions(
                    self.load_task(path, task_name)["when"]
                )[0]
                for group, expected in (([], False), (["node-1"], True)):
                    with self.subTest(task=task_name, group=group):
                        self.assertIs(
                            self.evaluate(
                                condition,
                                {"groups": {group_name: group}},
                            ),
                            expected,
                        )

    def test_csr_changed_condition(self):
        path = "tests/testcases/025_check-csr-request.yml"
        task_name = "Approve certificates"

        for stdout, expected in (
            ("", False),
            ("certificatesigningrequest approved", True),
        ):
            with self.subTest(stdout=stdout):
                self.assert_condition_results(
                    path,
                    task_name,
                    "changed_when",
                    {"certificate_approve": {"stdout": stdout}},
                    [expected],
                )

    def test_ansible_evaluator_expression_boundaries(self):
        iterator_sum = "(range(1, 3) | map('pow', 2)) + (range(1, 3) | map('pow', 3))"
        iterator_comparison = f"({iterator_sum}) == [1.0, 4.0, 1.0, 8.0]"

        with self.assertRaises(AnsibleBrokenConditionalError):
            self.evaluate(iterator_sum)
        self.assertTrue(self.evaluate(iterator_comparison))
