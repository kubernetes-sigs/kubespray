# -*- coding: utf-8 -*-
# Copyright the Kubespray contributors.
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

DOCUMENTATION = """
name: acquire_upgrade_slot
short_description: Acquire a concurrency slot before upgrading a node
description:
  - Blocks until a concurrency slot is free, then claims it by writing a lease
    file on the Ansible controller.
  - Together with M(release_upgrade_slot) this implements the sliding-window
    upgrade model - a node that finishes immediately frees its slot for the
    next waiting node, with no batch synchronisation point.
  - Only useful in a play running the built-in C(free) or C(host_pinned)
    strategy. Under C(linear) every host reaches this task before any host may
    proceed, so the play would deadlock.
  - Must be paired with a M(release_upgrade_slot) call in the C(always:)
    section of the surrounding block so the slot is freed even when the
    upgrade fails.
notes:
  - All coordination happens on the Ansible controller. C(delegate_to:) is
    neither needed nor supported - the action plugin never opens a connection
    to the managed node.
  - Leases live in C(~/.ansible/tmp/kubespray-upgrade-<run_id>/) with mode
    0700. The directory is owned by the user running ansible-playbook, which
    avoids the symlink races of a predictable path under C(/tmp).
  - Because a host waiting for a slot occupies an Ansible worker, the fork
    count must exceed the configured concurrency. The plugin clamps
    C(concurrency) to C(forks - 1) and warns once per run when it does so.
  - The failure marker written by M(release_upgrade_slot) is only consulted
    while a host waits for a slot. A host that already holds one finishes its
    upgrade even after another node failed - abandoning a half-drained node
    would leave the cluster in a worse state than completing it.
options:
  concurrency:
    description:
      - Maximum number of hosts allowed to hold a slot simultaneously.
      - Accepts a plain integer (C(5)) or a percentage string (C("20%")).
        Percentages are resolved against C(total_hosts), rounded down and
        clamped to a minimum of 1 - the same arithmetic ansible-core applies
        to C(serial), so a given percentage means the same under either
        upgrade strategy.
      - Clamped to C(forks - 1). Defaults to C(forks - 1) when omitted.
    type: raw
  per_group:
    description:
      - Optional per-group concurrency ceilings. Keys are Ansible group names,
        values are integers or percentage strings.
      - A host may start only when every group limit that applies to it has a
        free slot. The special key C(default) applies to hosts that are not a
        member of any other listed group.
      - A percentage here is taken of that group's own hosts, not of the whole
        play - C(calico_rr: "50%") means half of the route reflectors. Group
        membership is intersected with the play, so hosts the play does not
        target are not counted. C(default) is resolved against the hosts that
        match none of the other listed groups.
    type: dict
    default: {}
  total_hosts:
    description:
      - Number of hosts in the play, used as the denominator when
        C(concurrency) is a percentage. Pass
        C({{ ansible_play_hosts_all | length }}).
      - Use C(ansible_play_hosts_all), not C(ansible_play_hosts) - the latter
        excludes hosts that have already failed, so the window would silently
        narrow as a run degrades.
      - Not needed for C(per_group) percentages, which count the group's hosts
        themselves.
    type: int
  run_id:
    description:
      - Identifier scoping the lease directory, so that concurrent
        ansible-playbook invocations do not share slots.
      - Limited to letters, digits, dot, dash and underscore, because the
        value becomes a directory name.
      - Defaults to a value derived from Ansible's own per-run controller temp
        directory, which is unique per invocation and stable across forked
        workers.
    type: str
  poll_interval:
    description:
      - Seconds between slot-availability checks while waiting.
    type: float
    default: 5.0
  lease_ttl:
    description:
      - Age in seconds after which a lease is considered abandoned (written by
        an Ansible process that was killed) and removed. Must comfortably
        exceed the duration of a single node upgrade.
    type: int
    default: 3600
  timeout:
    description:
      - Maximum seconds to wait for a slot before failing the task.
      - C(0) waits indefinitely, which is the safe default - with a large
        cluster and a small window the last node legitimately waits a long
        time. Abandoned leases are reclaimed via C(lease_ttl) regardless.
    type: int
    default: 0
  abort_on_failure:
    description:
      - When another host has already failed its upgrade, fail immediately
        instead of claiming a slot.
      - This restores the intent of C(any_errors_fatal), which ansible-core
        implements only in the C(linear) strategy and silently ignores under
        C(free) and C(host_pinned).
    type: bool
    default: true
"""

EXAMPLES = """
- name: Acquire upgrade slot
  acquire_upgrade_slot:
    concurrency: "{{ upgrade_node_concurrency }}"
    per_group: "{{ upgrade_per_group_concurrency }}"
    total_hosts: "{{ ansible_play_hosts_all | length }}"
"""

RETURN = """
slot_acquired:
  description: Always C(true) - the task only returns once the slot is granted.
  type: bool
  returned: success
active_slots:
  description: Number of held leases at the moment this slot was granted.
  type: int
  returned: success
concurrency:
  description: The effective window size after percentage resolution and clamping.
  type: int
  returned: success
waited_seconds:
  description: How long this host waited for a slot.
  type: float
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

# Bucket used for hosts that match none of the explicitly listed groups.
DEFAULT_BUCKET = "__default__"

FAILURE_MARKER = "UPGRADE_FAILED"

# run_id becomes a directory name, so keep it to characters that cannot walk
# out of ~/.ansible/tmp.
SAFE_RUN_ID = re.compile(r"[A-Za-z0-9._-]+")

VALID_ARGS = frozenset((
    "concurrency",
    "per_group",
    "total_hosts",
    "run_id",
    "poll_interval",
    "lease_ttl",
    "timeout",
    "abort_on_failure",
))


class ActionModule(ActionBase):
    """Block until an upgrade concurrency slot is available, then claim it."""

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
                "Unsupported parameters for acquire_upgrade_slot: %s. "
                "Supported: %s" % (", ".join(sorted(unknown)), ", ".join(sorted(VALID_ARGS)))
            )

        hostname = task_vars.get("inventory_hostname", "unknown")
        group_names = set(task_vars.get("group_names") or [])

        total_hosts = to_int(args.get("total_hosts"), "total_hosts", minimum=1)
        poll_interval = to_float(
            args.get("poll_interval"), "poll_interval", minimum=0.1, default=5.0,
        )
        lease_ttl = to_int(args.get("lease_ttl"), "lease_ttl", minimum=1, default=3600)
        timeout = to_int(args.get("timeout"), "timeout", minimum=0, default=0)
        abort_on_failure = to_bool(
            args.get("abort_on_failure"), "abort_on_failure", default=True,
        )

        per_group_arg = args.get("per_group") or {}
        if not isinstance(per_group_arg, dict):
            raise AnsibleActionFail(
                "acquire_upgrade_slot: 'per_group' must be a mapping of group name "
                "to a limit, got %r" % (per_group_arg,)
            )

        forks = current_forks()
        if forks < 2:
            raise AnsibleActionFail(
                "acquire_upgrade_slot needs at least 2 forks: a host waiting for a "
                "slot occupies a worker, so with forks=1 no host could ever make "
                "progress. Raise forks (ansible.cfg [defaults] forks, ANSIBLE_FORKS "
                "or -f) to at least 2."
            )
        # A waiting host holds a worker, so the window must leave one worker
        # free for a host that could still be admitted.
        ceiling = forks - 1

        lease_dir = lease_directory(args.get("run_id"))
        # Created before the limits are resolved so that warn_once() has
        # somewhere to record what it already said. Check mode creates nothing.
        if not self._task.check_mode:
            mkdir_private(lease_dir)

        def warn(key, message):
            warn_once(lease_dir, key, message)

        concurrency = resolve_concurrency(
            args.get("concurrency"), total_hosts, ceiling, "concurrency",
            default=ceiling, warn=warn,
            hint="total_hosts was not supplied. Pass "
                 "total_hosts: \"{{ ansible_play_hosts_all | length }}\".",
        )
        per_group = {
            name: resolve_concurrency(
                value,
                group_denominator(name, per_group_arg, task_vars),
                ceiling,
                "per_group[%s]" % name,
                warn=warn,
                hint="the group holds no hosts in this play, so there is nothing "
                     "to take a percentage of.",
            )
            for name, value in per_group_arg.items()
        }

        if self._task.check_mode:
            result.update({
                "changed": False,
                "slot_acquired": True,
                "active_slots": 0,
                "concurrency": concurrency,
                "waited_seconds": 0.0,
                "msg": "check mode: a slot would be acquired",
            })
            return result

        lock_path = lease_dir / ".lock"
        lease_path = lease_dir / lease_filename(hostname)

        display.vv(
            "acquire_upgrade_slot: %s waiting for a slot "
            "(window=%d, per_group=%s, leases=%s)"
            % (hostname, concurrency, per_group or "{}", lease_dir)
        )

        started = time.monotonic()
        attempt = 0
        active = 0
        # One handle for the whole wait: the lock is per flock() call, so
        # reopening the file on every poll only adds syscalls.
        with open(lock_path, "a") as lock_fh:
            while True:
                attempt += 1
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
                try:
                    if abort_on_failure:
                        failure = read_failure_marker(lease_dir)
                        if failure:
                            raise AnsibleActionFail(
                                "Aborting upgrade of %s: node %s already failed%s. "
                                "No further nodes will be drained; see that node's "
                                "error above. Set upgrade_abort_on_failure=false to "
                                "keep going after a node failure."
                                % (hostname, failure.get("host", "?"),
                                   describe_failure(failure))
                            )

                    entries = reap_abandoned(
                        read_lease_entries(lease_dir), lease_ttl, lease_path,
                    )
                    active = len(entries)
                    holds_own_lease = any(path == lease_path for path, _ in entries)

                    # A lease of our own is never reclaimed by reap_abandoned(),
                    # so counting it would make this host wait for itself
                    # forever. It means the slot is already ours: an earlier run
                    # sharing the same run_id was killed while holding it, or
                    # the task was retried.
                    if holds_own_lease:
                        display.warning(
                            "acquire_upgrade_slot: %s already held a lease - left "
                            "behind by a killed run sharing this run_id, or the task "
                            "was retried. Reusing that slot instead of waiting for "
                            "it to expire." % hostname
                        )

                    if holds_own_lease or (active < concurrency and group_limits_ok(
                        group_names,
                        count_per_group([data for _, data in entries], per_group),
                        per_group,
                    )):
                        write_lease(lease_path, group_names)
                        waited = time.monotonic() - started
                        held = active if holds_own_lease else active + 1
                        display.vv(
                            "acquire_upgrade_slot: %s acquired a slot after %.1fs "
                            "(%d/%d in flight)"
                            % (hostname, waited, held, concurrency)
                        )
                        result.update({
                            "changed": False,
                            "slot_acquired": True,
                            "active_slots": held,
                            "concurrency": concurrency,
                            "waited_seconds": round(waited, 1),
                        })
                        return result
                finally:
                    fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)

                waited = time.monotonic() - started
                delay = poll_interval
                if timeout:
                    remaining = timeout - waited
                    if remaining <= 0:
                        raise AnsibleActionFail(
                            "acquire_upgrade_slot: %s waited %.0fs for a free slot "
                            "(limit %ds, %d/%d in flight). Either a node upgrade is "
                            "stuck or upgrade_slot_timeout is too low."
                            % (hostname, waited, timeout, active, concurrency)
                        )
                    # Do not overshoot the deadline by up to a poll interval.
                    delay = min(poll_interval, remaining)

                display.vvv(
                    "acquire_upgrade_slot: %s still waiting (attempt %d, %d/%d in flight)"
                    % (hostname, attempt, active, concurrency)
                )
                time.sleep(delay)


# ---------------------------------------------------------------------------
# Helpers, kept at module level so the unit tests can exercise them directly.
#
# to_bool, write_json_atomic, safe_run_id, lease_filename, lease_directory,
# ansible_home_tmp and ansible_local_tmp are duplicated in
# release_upgrade_slot.py. Both plugins are loaded straight from
# plugins/action/, which is not an importable package, so there is nowhere to
# share them from that works both in the repository and in the built
# collection. Keep the two copies in step - the unit tests assert that they
# agree on the on-disk format and on the lease paths they derive.
# ---------------------------------------------------------------------------

def to_bool(value, label, default=None):
    """Coerce an Ansible-style boolean, rejecting anything ambiguous.

    Guessing here is dangerous: ``abort_on_failure`` defaults to true, so a
    typo silently turning into false would disable the safety net without a
    word of warning.
    """
    if value is None:
        return default
    try:
        return convert_bool(value)
    except TypeError as exc:
        raise AnsibleActionFail(
            "acquire_upgrade_slot: '%s' must be a boolean, got %r" % (label, value)
        ) from exc


def to_int(value, label, minimum=None, default=None):
    """Coerce an integer argument, reporting bad input as a task failure."""
    if value is None or value == "":
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise AnsibleActionFail(
            "acquire_upgrade_slot: '%s' must be an integer, got %r" % (label, value)
        ) from exc
    if minimum is not None and number < minimum:
        raise AnsibleActionFail(
            "acquire_upgrade_slot: '%s' must be at least %d, got %r"
            % (label, minimum, value)
        )
    return number


def to_float(value, label, minimum=None, default=None):
    """Coerce a float argument, reporting bad input as a task failure."""
    if value is None or value == "":
        return default
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise AnsibleActionFail(
            "acquire_upgrade_slot: '%s' must be a number, got %r" % (label, value)
        ) from exc
    if minimum is not None and number < minimum:
        raise AnsibleActionFail(
            "acquire_upgrade_slot: '%s' must be at least %s, got %r"
            % (label, minimum, value)
        )
    return number


def current_forks():
    """Return the fork count actually in effect for this run.

    ``CLIARGS`` carries the value ``-f/--forks`` was parsed into, which is
    where an explicit command line lands. The ``DEFAULT_FORKS`` fallback only
    matters outside a CLI run, such as under the unit tests.
    """
    try:
        from ansible import context

        forks = context.CLIARGS.get("forks")
        if forks:
            return int(forks)
    except Exception:  # noqa: BLE001 - CLIARGS is absent outside a CLI run
        pass

    try:
        from ansible import constants as C

        return int(C.DEFAULT_FORKS)
    except Exception:  # noqa: BLE001
        return 5


def resolve_concurrency(raw, denominator, ceiling, label, default=None,
                        warn=None, hint=None):
    """Resolve an integer or ``"N%"`` concurrency value into ``[1, ceiling]``.

    *denominator* is what a percentage is taken of: the play's host count for
    the global window, the group's host count for a per-group ceiling.
    """
    if raw is None or raw == "":
        if default is None:
            raise AnsibleActionFail("acquire_upgrade_slot: '%s' is required" % label)
        return default

    if isinstance(raw, str) and raw.strip().endswith("%"):
        if not denominator:
            raise AnsibleActionFail(
                "acquire_upgrade_slot: '%s' is the percentage %r but %s"
                % (label, raw,
                   hint or "there is no host count to resolve it against.")
            )
        try:
            fraction = float(raw.strip()[:-1]) / 100.0
        except ValueError as exc:
            raise AnsibleActionFail(
                "acquire_upgrade_slot: '%s' is not a valid percentage: %r" % (label, raw)
            ) from exc
        if fraction < 0:
            raise AnsibleActionFail(
                "acquire_upgrade_slot: '%s' must not be negative, got %r" % (label, raw)
            )
        # Round down with a floor of 1, matching ansible-core's pct_to_int()
        # so that "20%" selects the same number of hosts here as it does in
        # serial: under the linear strategy.
        value = max(1, int(fraction * int(denominator)))
    else:
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise AnsibleActionFail(
                "acquire_upgrade_slot: '%s' must be an integer or a percentage "
                "string, got %r" % (label, raw)
            ) from exc
        if value < 1:
            raise AnsibleActionFail(
                "acquire_upgrade_slot: '%s' must be at least 1, got %r" % (label, raw)
            )

    if value > ceiling:
        message = (
            "acquire_upgrade_slot: %s resolved to %d but is capped at %d "
            "(forks - 1). A host waiting for a slot occupies a worker, so a "
            "window that large would stall the play. Raise forks to widen it."
            % (label, value, ceiling)
        )
        if warn:
            warn("clamp-%s" % label, message)
        else:
            display.warning(message)
        value = ceiling
    return value


def group_denominator(name, per_group, task_vars):
    """Return how many of the play's hosts a per-group percentage refers to.

    A ceiling written for a group is about that group, so C(calico_rr: "50%")
    means half of the route reflectors - not half of the cluster. Inventory
    membership is intersected with the play, because the worker play excludes
    the control plane while C(groups) does not.
    """
    play_hosts = set(task_vars.get("ansible_play_hosts_all") or [])
    groups = task_vars.get("groups") or {}

    def members(group_name):
        hosts = set(groups.get(group_name) or [])
        return hosts & play_hosts if play_hosts else hosts

    if name != "default":
        return len(members(name))

    # The default bucket covers whatever is left over once every explicitly
    # listed group has been accounted for.
    listed = set()
    for other in per_group:
        if other != "default":
            listed |= members(other)
    return len(play_hosts - listed)


def warn_once(lease_dir, key, message):
    """Emit *message* once for the whole run rather than once per host.

    Every worker resolves the same configuration, so a plain warning would
    repeat the identical line for every node in the play. The marker is
    created with O_EXCL, which is atomic on its own - no need to take the slot
    lock, which is not held yet at configuration time.
    """
    marker = lease_dir / (".warned-%s" % re.sub(r"[^A-Za-z0-9_.-]", "-", key))
    try:
        os.close(os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError:
        return
    except OSError:
        # No lease directory yet (check mode). Better loud than silent.
        pass
    display.warning(message)


def lease_directory(run_id=None):
    """Return the directory holding this run's leases.

    By default the leases live inside Ansible's own controller-side temp
    directory. That directory is created once per invocation, inherited by
    every worker across ``fork()``, and removed when the run ends - so slots
    are naturally scoped to one playbook run and leave nothing behind. It also
    sits under ``$HOME`` with mode 0700, unlike a predictable path in ``/tmp``
    that a co-tenant could race.
    """
    if run_id:
        return ansible_home_tmp() / ("kubespray-upgrade-%s" % safe_run_id(run_id))

    local_tmp = ansible_local_tmp()
    if local_tmp:
        return local_tmp / "kubespray-upgrade"

    # Only reached if ansible-core stops exposing its local temp directory.
    # The process group is stable across forked workers, but two playbooks
    # started from one non-interactive shell script would share it.
    return ansible_home_tmp() / ("kubespray-upgrade-%s" % os.getpgid(0))


def safe_run_id(run_id):
    """Reject a run_id that would not stay inside ``~/.ansible/tmp``."""
    text = str(run_id)
    if text in (".", "..") or not SAFE_RUN_ID.fullmatch(text):
        raise AnsibleActionFail(
            "acquire_upgrade_slot: 'run_id' becomes a directory name and may only "
            "contain letters, digits, '.', '-' and '_', got %r" % (run_id,)
        )
    return text


def lease_filename(hostname):
    """Return the lease file name for *hostname*.

    Only the path separator is dangerous - it would let an inventory name
    place the lease outside the run's directory. Everything else a filesystem
    accepts (the colons of an IPv6 address, dots) is kept verbatim so that log
    messages keep naming the real host.
    """
    text = str(hostname)
    if "/" in text or "\0" in text or text in (".", ".."):
        raise AnsibleActionFail(
            "acquire_upgrade_slot: inventory_hostname %r cannot be used as a lease "
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


def mkdir_private(path):
    """Create *path*, and any missing parents, all at mode 0700.

    ``Path.mkdir(parents=True, mode=...)`` only applies *mode* to the leaf
    directory - missing parents fall back to Ansible's own recursive mkdir,
    created with the default umask-derived permissions. Walk up by hand so a
    freshly created ``~/.ansible`` or ``~/.ansible/tmp`` cannot end up
    world-readable.
    """
    if path.is_dir():
        return
    mkdir_private(path.parent)
    path.mkdir(mode=0o700, exist_ok=True)


def write_json_atomic(path, data):
    """Write *data* as JSON via a temp file + rename, so a concurrent reader
    that glob()s the directory never observes a partially written file."""
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(json.dumps(data))
    os.rename(tmp_path, path)


def write_lease(lease_path, group_names):
    """Write a lease file, atomically so a concurrent reader sees it whole."""
    write_json_atomic(lease_path, {
        "acquired_at": time.time(),
        "groups": sorted(group_names),
    })


def read_lease_entries(lease_dir):
    """Return ``(path, data)`` for every lease currently held."""
    entries = []
    for path in sorted(lease_dir.glob("*.lease")):
        try:
            entries.append((path, json.loads(path.read_text())))
        except (OSError, ValueError):
            # The lease was released between glob() and read(); it holds no slot.
            continue
    return entries


def reap_abandoned(entries, ttl, keep_path):
    """Drop leases older than *ttl*, left behind by a killed Ansible process.

    *keep_path* - the caller's own lease - is never reclaimed here. The caller
    decides what to do with it, because for that one file "abandoned" means
    "already mine" rather than "someone else's stale slot".
    """
    cutoff = time.time() - ttl
    alive = []
    for path, data in entries:
        if path != keep_path and data.get("acquired_at", 0) < cutoff:
            path.unlink(missing_ok=True)
            display.warning(
                "acquire_upgrade_slot: reclaimed the slot held by %s, its lease "
                "was older than upgrade_slot_lease_ttl (%ds). If that node is "
                "still upgrading, raise the TTL." % (path.stem, ttl)
            )
            continue
        alive.append((path, data))
    return alive


def read_failure_marker(lease_dir):
    """Return the recorded first failure, or ``None`` while the run is healthy."""
    try:
        return json.loads((lease_dir / FAILURE_MARKER).read_text())
    except (OSError, ValueError):
        return None


def describe_failure(failure):
    """Render the ``task``/``reason`` of a marker as an explanatory clause.

    The task name alone is often the wrong thing to show: a role that wraps a
    step in its own ``rescue:`` re-raises through a task of its choosing, so a
    failed drain surfaces as ``Fail after rescue``. The reason carries what
    actually went wrong, so prefer to show both.
    """
    task = failure.get("task")
    reason = failure.get("reason")
    if task and reason:
        return " in task '%s': %s" % (task, reason)
    if task:
        return " in task '%s'" % task
    if reason:
        return ": %s" % reason
    return ""


def count_per_group(leases, per_group):
    """Count held leases per tracked group."""
    explicit = set(per_group) - {"default"}
    counts = {}
    for lease in leases:
        groups = set(lease.get("groups") or [])
        matched = False
        for name in explicit & groups:
            counts[name] = counts.get(name, 0) + 1
            matched = True
        if "default" in per_group and not matched:
            counts[DEFAULT_BUCKET] = counts.get(DEFAULT_BUCKET, 0) + 1
    return counts


def group_limits_ok(group_names, counts, per_group):
    """Return True when every group ceiling applying to this host has room."""
    if not per_group:
        return True

    explicit = set(per_group) - {"default"}
    for name in explicit & group_names:
        if counts.get(name, 0) >= per_group[name]:
            display.vvv(
                "acquire_upgrade_slot: deferred, group '%s' is at its limit of %d"
                % (name, per_group[name])
            )
            return False

    if "default" in per_group and not (group_names & explicit):
        if counts.get(DEFAULT_BUCKET, 0) >= per_group["default"]:
            display.vvv(
                "acquire_upgrade_slot: deferred, the default group limit of %d is reached"
                % per_group["default"]
            )
            return False

    return True
