"""Custom ansible-lint rule to enforce FQCN for the kube module."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task
    from ruamel.yaml.comments import CommentedMap, CommentedSeq


class FQCNKubeRule(AnsibleLintRule):
    """Use FQCN for kubespray module actions."""

    id = "fqcn-kubespray"
    description = (
        "The 'kube' module must be referenced by its fully qualified collection name "
        "'kubernetes_sigs.kubespray.kube'. Using the short name breaks when the "
        "collection is installed via ansible-galaxy and its playbooks are imported by "
        "other playbooks."
    )
    severity: ClassVar[str] = "HIGH"
    tags: ClassVar[list[str]] = ["formatting"]

    # this typically relates to ansible-lint release and the field is mandatory
    # to suppress a warning.
    # set it to the closest kubespray version instead
    version_changed: ClassVar[str] = "2.31.1"

    # Short names that should be replaced with FQCN
    _SHORT_TO_FQCN: ClassVar[dict[str, str]] = {
        "kube": "kubernetes_sigs.kubespray.kube",
    }

    def matchtask(self, task: Task, file: Lintable | None = None) -> list[MatchError]:
        """Check if a task uses a module name that should be replaced with its FQCN.

        Returns a list containing a single ``MatchError`` when the task's module
        is found in ``_SHORT_TO_FQCN``, or an empty list otherwise.
        """
        module = task["action"]["__ansible_module_original__"]
        if module in self._SHORT_TO_FQCN:
            fqcn = self._SHORT_TO_FQCN[module]
            return [
                self.create_matcherror(
                    message=f"Use FQCN for kubespray module actions ({module}).",
                    details=f"Use `{fqcn}` instead.",
                    filename=file,
                    lineno=task["__line__"],
                    tag="fqcn[kube]",
                ),
            ]
        return []

    def transform(
        self,
        match: ansiblelint.errors.MatchError,  # noqa: F821
        _: Lintable,
        data: CommentedMap | CommentedSeq,
    ) -> None:
        """Auto-fix: rename the short module key to FQCN in-place."""
        target_task = self._seek(data, match.yaml_path)
        if target_task is None:
            return

        for short, fqcn in self._SHORT_TO_FQCN.items():
            if short in target_task:
                # Preserve the value and insert position by renaming the key
                self._rename_key(target_task, short, fqcn)
                match.fixed = True
                break

    @staticmethod
    def _seek(
        data: CommentedMap | CommentedSeq,
        yaml_path: list,
    ) -> CommentedMap | None:
        """Walk the parsed YAML tree to the task mapping."""
        node = data
        for segment in yaml_path:
            if isinstance(node, list):
                node = node[int(segment)]
            elif isinstance(node, dict):
                node = node[segment]
            else:
                return None
        return node if isinstance(node, dict) else None

    @staticmethod
    def _rename_key(
        task: CommentedMap,
        old_key: str,
        new_key: str,
    ) -> None:
        """Rename a key in a CommentedMap while preserving order and comments."""
        # Collect all items in order, replacing the key name
        items = list(task.items())
        comments = task.ca.items.copy() if hasattr(task, "ca") else {}

        task.clear()
        for _, (k, v) in enumerate(items):
            task[new_key if k == old_key else k] = v

        # Restore comment on the renamed key
        if old_key in comments:
            task.ca.items[new_key] = comments[old_key]
