# -*- coding: utf-8 -*-
# Copyright the Kubespray contributors.
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

DOCUMENTATION = """
name: release_upgrade_slot
short_description: Release the concurrency slot held by this node
description:
  - Removes this host's lease so the next waiting node may start, and
    optionally records that the upgrade failed.
  - Belongs in the C(always:) section of the block that acquired the slot, so
    that a failed node still hands its slot back.
  - Releasing a slot that was never acquired is not an error, which keeps the
    task safe in C(always:) even when M(acquire_upgrade_slot) itself failed.
notes:
  - Runs entirely on the Ansible controller and opens no connection to the
    managed node.
  - With C(mark_failed) the plugin writes a marker that makes every subsequent
    M(acquire_upgrade_slot) fail fast. Only the first failure is recorded, so
    the reported node is the one that actually broke the run.
options:
  mark_failed:
    description:
      - Record that this host failed its upgrade, stopping any node that has
        not yet been drained.
      - Use it from a C(rescue:) section; the plain C(always:) release should
        leave it at the default.
    type: bool
    default: false
  task:
    description:
      - Name of the task that failed, stored in the marker so the abort
        message can point at it. Pass C({{ ansible_failed_task.name }}).
      - On its own this is often not enough. A role that wraps a step in its
        own C(block)/C(rescue) re-raises through a task of its choosing, so
        the name that reaches this plugin is that re-raise - for a failed
        drain, C(upgrade/pre-upgrade) reports C(Fail after rescue) rather than
        C(Drain node). Pass C(reason) as well.
    type: str
  reason:
    description:
      - Message of the failure, stored alongside C(task) so the abort message
        can say what went wrong rather than only where. Pass
        C({{ ansible_failed_result.msg }}).
      - Truncated to 200 characters, because a module failure can carry an
        entire command's stderr.
    type: str
  run_id:
    description:
      - Must match the C(run_id) given to M(acquire_upgrade_slot). Defaults to
        the same derived per-run value.
      - Limited to letters, digits, dot, dash and underscore, because the
        value becomes a directory name.
    type: str
"""

EXAMPLES = """
- name: Release upgrade slot
  release_upgrade_slot:

- name: Stop the rollout after a failed node
  release_upgrade_slot:
    mark_failed: true
    task: "{{ ansible_failed_task.name | default('unknown') }}"
    reason: "{{ ansible_failed_result.msg | default('') }}"
"""

RETURN = """
slot_released:
  description: Whether a lease was actually removed.
  type: bool
  returned: success
failure_recorded:
  description: Whether this call wrote the failure marker.
  type: bool
  returned: success
"""

import fcntl
import json
import os
import re
import time
from pathlib import Path

from ansible.errors import AnsibleActionFail
from ansible.module_utils.parsing.convert_bool import boolean as convert_bool
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

FAILURE_MARKER = "UPGRADE_FAILED"

# run_id becomes a directory name, so keep it to characters that cannot walk
# out of ~/.ansible/tmp.
SAFE_RUN_ID = re.compile(r"[A-Za-z0-9._-]+")

VALID_ARGS = frozenset(("mark_failed", "task", "reason", "run_id"))

# A module failure can carry an entire command's stderr; the abort message only
# needs enough of it to point at the cause.
MAX_REASON = 200


class ActionModule(ActionBase):
    """Hand back the upgrade slot held by this host."""

    TRANSFERS_FILES = False
    _requires_connection = False
    _supports_check_mode = True
    _supports_async = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        del tmp
        task_vars = task_vars or {}

        args = self._task.args
        unknown = set(args) - VALID_ARGS
        if unknown:
            raise AnsibleActionFail(
                "Unsupported parameters for release_upgrade_slot: %s. "
                "Supported: %s" % (", ".join(sorted(unknown)), ", ".join(sorted(VALID_ARGS)))
            )

        hostname = task_vars.get("inventory_hostname", "unknown")
        mark_failed = to_bool(args.get("mark_failed"), "mark_failed", default=False)
        # Only a rescue: section can name the failing task; from always: the
        # caller has nothing to pass and the marker stays without one.
        failed_task = args.get("task") or None
        failed_reason = summarise(args.get("reason"))

        lease_dir = lease_directory(args.get("run_id"))

        if self._task.check_mode:
            result.update({
                "changed": False,
                "slot_released": False,
                "failure_recorded": False,
                "msg": "check mode: the slot would be released",
            })
            return result

        if not lease_dir.is_dir():
            # No slot was ever acquired - graceful_rolling is off, or the play
            # failed before the acquire task ran.
            result.update({
                "changed": False,
                "slot_released": False,
                "failure_recorded": False,
                "msg": "no lease directory, nothing to release",
            })
            return result

        lease_path = lease_dir / lease_filename(hostname)
        marker_path = lease_dir / FAILURE_MARKER
        released = False
        recorded = False

        with open(lease_dir / ".lock", "a") as lock_fh:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
            try:
                if mark_failed and not marker_path.exists():
                    write_json_atomic(marker_path, {
                        "host": hostname,
                        "task": failed_task,
                        "reason": failed_reason,
                        "failed_at": time.time(),
                    })
                    recorded = True
                    display.warning(
                        "release_upgrade_slot: %s failed to upgrade. Nodes that "
                        "have not started yet will abort instead of draining."
                        % hostname
                    )

                if lease_path.exists():
                    lease_path.unlink()
                    released = True
                    display.vv("release_upgrade_slot: %s released its slot" % hostname)
                else:
                    display.vv(
                        "release_upgrade_slot: %s held no slot (already released "
                        "or never acquired)" % hostname
                    )
            finally:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)

        result.update({
            "changed": False,
            "slot_released": released,
            "failure_recorded": recorded,
        })
        return result


# ---------------------------------------------------------------------------
# The helpers below are duplicated in acquire_upgrade_slot.py. Both plugins are
# loaded straight from plugins/action/, which is not an importable package, so
# there is nowhere to share them from that works both in the repository and in
# the built collection. Keep the two copies in step - the unit tests assert
# that they agree on the on-disk format and on the lease paths they derive.
# ---------------------------------------------------------------------------

def summarise(reason):
    """Condense a failure message to one line that fits an abort message."""
    if not reason:
        return None
    text = " ".join(str(reason).split())
    if len(text) > MAX_REASON:
        text = text[:MAX_REASON - 1].rstrip() + "…"
    return text or None


def to_bool(value, label, default=None):
    """Coerce an Ansible-style boolean, rejecting anything ambiguous.

    Guessing here is dangerous: a typo silently turning into false would
    quietly skip the failure marker.
    """
    if value is None:
        return default
    try:
        return convert_bool(value)
    except TypeError as exc:
        raise AnsibleActionFail(
            "release_upgrade_slot: '%s' must be a boolean, got %r" % (label, value)
        ) from exc


def write_json_atomic(path, data):
    """Write *data* as JSON via a temp file + rename, so a concurrent reader
    that glob()s the directory never observes a partially written file."""
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(json.dumps(data))
    os.rename(tmp_path, path)


def lease_directory(run_id=None):
    """Resolve the lease directory exactly as acquire_upgrade_slot does."""
    if run_id:
        return ansible_home_tmp() / ("kubespray-upgrade-%s" % safe_run_id(run_id))

    local_tmp = ansible_local_tmp()
    if local_tmp:
        return local_tmp / "kubespray-upgrade"

    return ansible_home_tmp() / ("kubespray-upgrade-%s" % os.getpgid(0))


def safe_run_id(run_id):
    """Reject a run_id that would not stay inside ``~/.ansible/tmp``."""
    text = str(run_id)
    if text in (".", "..") or not SAFE_RUN_ID.fullmatch(text):
        raise AnsibleActionFail(
            "release_upgrade_slot: 'run_id' becomes a directory name and may only "
            "contain letters, digits, '.', '-' and '_', got %r" % (run_id,)
        )
    return text


def lease_filename(hostname):
    """Return the lease file name for *hostname*, as acquire_upgrade_slot does."""
    text = str(hostname)
    if "/" in text or "\0" in text or text in (".", ".."):
        raise AnsibleActionFail(
            "release_upgrade_slot: inventory_hostname %r cannot be used as a lease "
            "file name. Rename the host in the inventory." % (hostname,)
        )
    return "%s.lease" % text


def ansible_home_tmp():
    """Return ``~/.ansible/tmp``, the parent of Ansible's per-run temp dirs."""
    return Path(os.path.expanduser("~/.ansible/tmp"))


def ansible_local_tmp():
    """Return Ansible's per-run controller temp directory, if it exists."""
    try:
        from ansible import constants as C

        path = Path(str(C.DEFAULT_LOCAL_TMP))
        return path if path.is_dir() else None
    except Exception:  # noqa: BLE001
        return None
