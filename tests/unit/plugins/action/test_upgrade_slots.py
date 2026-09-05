# Copyright the Kubespray contributors.
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the upgrade slot action plugins.

The plugins live outside any importable package, so they are loaded by path
the same way ansible-core's action loader finds them.
"""

import importlib.util
import json
import stat
import sys
import time
from pathlib import Path

import pytest
from ansible.errors import AnsibleActionFail

PLUGIN_DIR = Path(__file__).resolve().parents[4] / "plugins" / "action"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, PLUGIN_DIR / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


acquire = _load("acquire_upgrade_slot")
release = _load("release_upgrade_slot")


# ---------------------------------------------------------------------------
# A minimal stand-in for the ansible-core objects an action plugin is handed,
# so the run() methods can be exercised without a playbook.
# ---------------------------------------------------------------------------

class _FakeShell:
    tmpdir = None


class _FakeConnection:
    def __init__(self):
        self._shell = _FakeShell()


class _FakeTask:
    def __init__(self, action, args, check_mode=False):
        self.action = action
        self.args = args
        self.check_mode = check_mode
        self.async_val = 0


def make_action(module, name, args, check_mode=False):
    action = module.ActionModule.__new__(module.ActionModule)
    action._task = _FakeTask(name, args, check_mode)
    action._connection = _FakeConnection()
    return action


@pytest.fixture
def lease_dir(tmp_path, monkeypatch):
    """Point both plugins at a throwaway lease directory."""
    from ansible import constants as C

    monkeypatch.setattr(C, "DEFAULT_LOCAL_TMP", str(tmp_path), raising=False)
    return tmp_path / "kubespray-upgrade"


@pytest.fixture
def forks(monkeypatch):
    """Pin the fork count so the concurrency ceiling is predictable."""
    from ansible import context

    monkeypatch.setattr(context, "CLIARGS", {"forks": 20}, raising=False)


@pytest.fixture
def clock(monkeypatch):
    """Replace the wait loop's clock so tests never actually sleep."""
    state = {"now": 0.0, "on_sleep": None}

    def sleep(seconds):
        state["now"] += seconds
        if state["on_sleep"]:
            state["on_sleep"](state["now"])

    monkeypatch.setattr(time, "monotonic", lambda: state["now"])
    monkeypatch.setattr(time, "sleep", sleep)
    return state


def put_lease(directory, hostname, age=0.0, groups=()):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("%s.lease" % hostname)
    path.write_text(json.dumps({
        "acquired_at": time.time() - age,
        "groups": list(groups),
    }))
    return path


class TestResolveConcurrency:
    def test_plain_integer(self):
        assert acquire.resolve_concurrency(3, 10, 19, "c") == 3

    def test_percentage_of_play_hosts(self):
        assert acquire.resolve_concurrency("20%", 10, 19, "c") == 2

    def test_percentage_rounds_down_like_serial(self):
        # ansible-core's pct_to_int() truncates, so the same percentage has to
        # select the same number of hosts as serial: does under linear.
        assert acquire.resolve_concurrency("25%", 10, 19, "c") == 2
        assert acquire.resolve_concurrency("29%", 10, 19, "c") == 2
        assert acquire.resolve_concurrency("30%", 10, 19, "c") == 3

    def test_percentage_never_rounds_down_to_zero(self):
        # A one-node-at-a-time window is still a window; zero would deadlock.
        assert acquire.resolve_concurrency("1%", 10, 19, "c") == 1

    def test_clamped_to_ceiling(self):
        # A host waiting for a slot holds a worker, so the window cannot reach
        # the fork count without stalling the play.
        assert acquire.resolve_concurrency(100, 10, 19, "c") == 19
        assert acquire.resolve_concurrency("100%", 10, 19, "c") == 10

    def test_missing_value_uses_default(self):
        assert acquire.resolve_concurrency(None, 10, 19, "c", default=7) == 7

    def test_missing_value_without_default_is_an_error(self):
        with pytest.raises(AnsibleActionFail, match="is required"):
            acquire.resolve_concurrency(None, 10, 19, "c")

    def test_percentage_without_a_denominator_is_an_error(self):
        with pytest.raises(AnsibleActionFail, match="no host count"):
            acquire.resolve_concurrency("20%", None, 19, "c")

    def test_the_caller_can_supply_an_actionable_hint(self):
        with pytest.raises(AnsibleActionFail, match="pass total_hosts"):
            acquire.resolve_concurrency(
                "20%", 0, 19, "c", hint="pass total_hosts.",
            )

    def test_clamping_goes_through_the_caller_warn_hook(self):
        seen = []
        acquire.resolve_concurrency(100, 10, 19, "c", warn=lambda k, m: seen.append(k))
        assert seen == ["clamp-c"]

    @pytest.mark.parametrize("bad", ["abc", "%", "1.2.3", None])
    def test_rejects_garbage(self, bad):
        with pytest.raises(AnsibleActionFail):
            acquire.resolve_concurrency(bad, 10, 19, "c")

    def test_rejects_zero_and_negative(self):
        with pytest.raises(AnsibleActionFail, match="at least 1"):
            acquire.resolve_concurrency(0, 10, 19, "c")
        with pytest.raises(AnsibleActionFail, match="at least 1"):
            acquire.resolve_concurrency(-1, 10, 19, "c")

    def test_rejects_a_negative_percentage(self):
        with pytest.raises(AnsibleActionFail, match="must not be negative"):
            acquire.resolve_concurrency("-10%", 10, 19, "c")


class TestArgumentCoercion:
    """Bad input has to surface as a task failure, not a raw traceback."""

    def test_int_accepts_ansible_strings(self):
        assert acquire.to_int("7", "timeout") == 7

    def test_int_uses_the_default_when_unset(self):
        assert acquire.to_int(None, "timeout", default=3) == 3
        assert acquire.to_int("", "timeout", default=3) == 3

    def test_int_rejects_garbage(self):
        with pytest.raises(AnsibleActionFail, match="must be an integer"):
            acquire.to_int("soon", "timeout")

    def test_int_enforces_a_minimum(self):
        with pytest.raises(AnsibleActionFail, match="at least 1"):
            acquire.to_int(0, "lease_ttl", minimum=1)

    def test_float_accepts_ansible_strings(self):
        assert acquire.to_float("2.5", "poll_interval") == 2.5

    def test_float_rejects_garbage(self):
        with pytest.raises(AnsibleActionFail, match="must be a number"):
            acquire.to_float("often", "poll_interval")

    def test_float_enforces_a_minimum(self):
        # time.sleep() would raise on a negative interval.
        with pytest.raises(AnsibleActionFail, match="at least"):
            acquire.to_float(-1, "poll_interval", minimum=0.1)


class TestCurrentForks:
    def test_prefers_the_command_line(self, monkeypatch):
        from ansible import context

        monkeypatch.setattr(context, "CLIARGS", {"forks": 25}, raising=False)
        assert acquire.current_forks() == 25

    def test_falls_back_to_the_configured_default(self, monkeypatch):
        from ansible import constants as C
        from ansible import context

        monkeypatch.setattr(context, "CLIARGS", {}, raising=False)
        monkeypatch.setattr(C, "DEFAULT_FORKS", 12, raising=False)
        assert acquire.current_forks() == 12


class TestPerGroupLimits:
    def test_no_limits_always_admits(self):
        assert acquire.group_limits_ok({"kube_node"}, {}, {}) is True

    def test_blocks_when_an_explicit_group_is_full(self):
        leases = [{"groups": ["kube_node"]}, {"groups": ["kube_node"]}]
        limits = {"kube_node": 2}
        counts = acquire.count_per_group(leases, limits)
        assert counts == {"kube_node": 2}
        assert acquire.group_limits_ok({"kube_node"}, counts, limits) is False

    def test_admits_while_an_explicit_group_has_room(self):
        leases = [{"groups": ["kube_node"]}]
        limits = {"kube_node": 2}
        counts = acquire.count_per_group(leases, limits)
        assert acquire.group_limits_ok({"kube_node"}, counts, limits) is True

    def test_a_host_must_satisfy_every_group_it_belongs_to(self):
        leases = [{"groups": ["kube_node", "calico_rr"]}]
        limits = {"kube_node": 5, "calico_rr": 1}
        counts = acquire.count_per_group(leases, limits)
        assert acquire.group_limits_ok({"kube_node"}, counts, limits) is True
        assert acquire.group_limits_ok({"kube_node", "calico_rr"}, counts, limits) is False

    def test_untracked_groups_are_ignored(self):
        leases = [{"groups": ["some_other_group"]}]
        limits = {"kube_node": 1}
        counts = acquire.count_per_group(leases, limits)
        assert counts == {}
        assert acquire.group_limits_ok({"kube_node"}, counts, limits) is True

    def test_default_bucket_only_covers_unlisted_hosts(self):
        leases = [{"groups": ["misc"]}, {"groups": ["kube_node"]}]
        limits = {"kube_node": 5, "default": 1}
        counts = acquire.count_per_group(leases, limits)
        assert counts == {"kube_node": 1, acquire.DEFAULT_BUCKET: 1}
        # 'misc' falls into the full default bucket.
        assert acquire.group_limits_ok({"misc"}, counts, limits) is False
        # kube_node is explicitly listed, so the default ceiling does not apply.
        assert acquire.group_limits_ok({"kube_node"}, counts, limits) is True


class TestGroupDenominator:
    """A per-group percentage is about that group, not about the cluster."""

    TASK_VARS = {
        "ansible_play_hosts_all": ["n1", "n2", "n3", "n4", "rr1", "rr2"],
        "groups": {
            "all": ["cp1", "n1", "n2", "n3", "n4", "rr1", "rr2"],
            "kube_node": ["cp1", "n1", "n2", "n3", "n4"],
            "calico_rr": ["rr1", "rr2"],
        },
    }

    def test_counts_the_groups_own_hosts(self):
        assert acquire.group_denominator("calico_rr", {}, self.TASK_VARS) == 2

    def test_hosts_outside_the_play_do_not_count(self):
        # The worker play excludes the control plane, but groups['kube_node']
        # still lists it.
        assert acquire.group_denominator("kube_node", {}, self.TASK_VARS) == 4

    def test_an_unknown_group_has_no_hosts(self):
        assert acquire.group_denominator("gpu_nodes", {}, self.TASK_VARS) == 0

    def test_default_covers_whatever_no_listed_group_claims(self):
        per_group = {"calico_rr": 1, "default": "50%"}
        assert acquire.group_denominator("default", per_group, self.TASK_VARS) == 4

    def test_default_is_empty_once_every_host_is_listed(self):
        per_group = {"kube_node": 1, "calico_rr": 1, "default": 1}
        assert acquire.group_denominator("default", per_group, self.TASK_VARS) == 0

    def test_half_the_route_reflectors_is_one_not_three(self):
        # The whole point of the change: "50%" under calico_rr used to be
        # resolved against the six hosts of the play.
        denominator = acquire.group_denominator("calico_rr", {}, self.TASK_VARS)
        assert acquire.resolve_concurrency("50%", denominator, 19, "per_group") == 1


class TestWarnOnce:
    def test_the_first_caller_warns_and_the_rest_stay_quiet(self, tmp_path, monkeypatch):
        seen = []
        monkeypatch.setattr(acquire.display, "warning", seen.append)

        for _ in range(5):
            acquire.warn_once(tmp_path, "clamp-concurrency", "too wide")

        assert seen == ["too wide"]

    def test_different_keys_warn_independently(self, tmp_path, monkeypatch):
        seen = []
        monkeypatch.setattr(acquire.display, "warning", seen.append)

        acquire.warn_once(tmp_path, "clamp-concurrency", "a")
        acquire.warn_once(tmp_path, "clamp-per_group[calico_rr]", "b")

        assert seen == ["a", "b"]

    def test_a_key_that_is_not_a_filename_still_works(self, tmp_path, monkeypatch):
        monkeypatch.setattr(acquire.display, "warning", lambda message: None)

        acquire.warn_once(tmp_path, "clamp-per_group[a/b]", "x")

        assert [p.name for p in tmp_path.iterdir()] == [".warned-clamp-per_group-a-b-"]

    def test_without_a_directory_it_warns_rather_than_swallowing(self, tmp_path, monkeypatch):
        seen = []
        monkeypatch.setattr(acquire.display, "warning", seen.append)

        # Check mode never creates the lease directory.
        acquire.warn_once(tmp_path / "absent", "clamp-concurrency", "loud")

        assert seen == ["loud"]


class TestLeaseFiles:
    def test_write_then_read_round_trip(self, tmp_path):
        acquire.write_lease(tmp_path / "n1.lease", {"kube_node", "calico_rr"})
        entries = acquire.read_lease_entries(tmp_path)
        assert len(entries) == 1
        path, data = entries[0]
        assert path == tmp_path / "n1.lease"
        assert data["groups"] == ["calico_rr", "kube_node"]
        assert data["acquired_at"] <= time.time()

    def test_write_leaves_no_temporary_file_behind(self, tmp_path):
        acquire.write_lease(tmp_path / "n1.lease", set())
        assert [p.name for p in tmp_path.iterdir()] == ["n1.lease"]

    def test_partial_and_missing_files_hold_no_slot(self, tmp_path):
        (tmp_path / "broken.lease").write_text("{not json")
        assert acquire.read_lease_entries(tmp_path) == []

    def test_abandoned_leases_are_reclaimed(self, tmp_path):
        stale = put_lease(tmp_path, "dead", age=7200)
        fresh = put_lease(tmp_path, "alive")

        alive = acquire.reap_abandoned(
            acquire.read_lease_entries(tmp_path), 3600, tmp_path / "other.lease",
        )

        assert not stale.exists()
        assert fresh.exists()
        assert [path for path, _ in alive] == [fresh]

    def test_the_caller_own_lease_is_never_reclaimed(self, tmp_path):
        mine = put_lease(tmp_path, "me", age=7200)

        alive = acquire.reap_abandoned(
            acquire.read_lease_entries(tmp_path), 3600, mine,
        )

        assert mine.exists()
        assert [path for path, _ in alive] == [mine]


class TestWriteJsonAtomic:
    """Both plugins write their JSON files through this helper so that a
    reader glob()ing the directory never observes a half-written file."""

    @pytest.mark.parametrize("module", [acquire, release])
    def test_round_trip(self, tmp_path, module):
        path = tmp_path / "thing.json"
        module.write_json_atomic(path, {"a": 1})
        assert json.loads(path.read_text()) == {"a": 1}

    @pytest.mark.parametrize("module", [acquire, release])
    def test_leaves_no_temporary_file_behind(self, tmp_path, module):
        module.write_json_atomic(tmp_path / "thing.json", {})
        assert [p.name for p in tmp_path.iterdir()] == ["thing.json"]

    def test_acquire_and_release_produce_interchangeable_output(self, tmp_path):
        # release_upgrade_slot writes the failure marker; acquire_upgrade_slot
        # reads it back. Confirm the two independent copies of the helper
        # actually agree on the on-disk format.
        path = tmp_path / acquire.FAILURE_MARKER
        release.write_json_atomic(path, {"host": "n1", "task": None, "failed_at": 1.0})
        assert acquire.read_failure_marker(tmp_path)["host"] == "n1"


class TestFailureMarker:
    def test_absent_marker_reads_as_healthy(self, tmp_path):
        assert acquire.read_failure_marker(tmp_path) is None

    def test_marker_is_readable(self, tmp_path):
        (tmp_path / acquire.FAILURE_MARKER).write_text(
            json.dumps({"host": "n1", "failed_at": 1.0})
        )
        assert acquire.read_failure_marker(tmp_path)["host"] == "n1"

    def test_a_torn_write_reads_as_healthy_rather_than_crashing(self, tmp_path):
        # write_json_atomic can never leave this behind (rename is atomic),
        # but read_failure_marker must stay defensive regardless.
        (tmp_path / acquire.FAILURE_MARKER).write_text("")
        assert acquire.read_failure_marker(tmp_path) is None

    def test_acquire_and_release_agree_on_the_marker_name(self):
        assert acquire.FAILURE_MARKER == release.FAILURE_MARKER


class TestDescribeFailure:
    """A role with its own rescue: re-raises through a task of its choosing,
    so the task name alone can be useless - upgrade/pre-upgrade turns a failed
    drain into 'Fail after rescue'. The reason carries the actual cause."""

    def test_task_and_reason_are_both_shown(self):
        clause = acquire.describe_failure(
            {"task": "Fail after rescue", "reason": "Failed to drain node k8s-4"}
        )
        assert clause == " in task 'Fail after rescue': Failed to drain node k8s-4"

    def test_task_alone_still_works(self):
        assert acquire.describe_failure({"task": "Drain node"}) == " in task 'Drain node'"

    def test_reason_alone_still_works(self):
        assert acquire.describe_failure({"reason": "boom"}) == ": boom"

    def test_an_empty_marker_adds_nothing(self):
        assert acquire.describe_failure({}) == ""
        assert acquire.describe_failure({"task": None, "reason": None}) == ""


class TestSummarise:
    def test_collapses_whitespace_to_one_line(self):
        assert release.summarise("failed to drain\n  node  k8s-4\n") == \
            "failed to drain node k8s-4"

    def test_truncates_a_wall_of_stderr(self):
        text = release.summarise("x" * 500)
        assert len(text) == release.MAX_REASON
        assert text.endswith("…")

    def test_nothing_stays_nothing(self):
        assert release.summarise(None) is None
        assert release.summarise("") is None
        assert release.summarise("   ") is None


class TestMkdirPrivate:
    def test_creates_missing_parents_at_mode_0700(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        acquire.mkdir_private(target)

        for directory in (tmp_path / "a", tmp_path / "a" / "b", target):
            assert stat.S_IMODE(directory.stat().st_mode) == 0o700

    def test_idempotent_on_an_existing_directory(self, tmp_path):
        target = tmp_path / "a"
        target.mkdir(mode=0o700)

        acquire.mkdir_private(target)  # must not raise

        assert target.is_dir()


class TestLeaseDirectory:
    def test_both_plugins_derive_the_same_path(self, tmp_path, monkeypatch):
        from ansible import constants as C

        monkeypatch.setattr(C, "DEFAULT_LOCAL_TMP", str(tmp_path), raising=False)
        assert acquire.lease_directory() == release.lease_directory()
        assert acquire.lease_directory("abc") == release.lease_directory("abc")

    def test_defaults_inside_the_per_run_controller_tmpdir(self, tmp_path, monkeypatch):
        # Ansible removes that directory when the run ends, so leases from a
        # finished run never linger.
        from ansible import constants as C

        monkeypatch.setattr(C, "DEFAULT_LOCAL_TMP", str(tmp_path), raising=False)
        assert acquire.lease_directory() == tmp_path / "kubespray-upgrade"

    def test_falls_back_to_the_process_group_without_a_run_tmpdir(self, monkeypatch):
        from ansible import constants as C

        monkeypatch.setattr(C, "DEFAULT_LOCAL_TMP", "/nonexistent/xyz", raising=False)
        path = acquire.lease_directory()
        # Stable across forked workers, which is what matters for coordination.
        assert path.name == "kubespray-upgrade-%d" % __import__("os").getpgid(0)
        assert path.parent == Path.home() / ".ansible" / "tmp"

    def test_an_explicit_run_id_wins(self, tmp_path, monkeypatch):
        from ansible import constants as C

        monkeypatch.setattr(C, "DEFAULT_LOCAL_TMP", str(tmp_path), raising=False)
        path = acquire.lease_directory("abc")
        assert path.name == "kubespray-upgrade-abc"
        # Not /tmp: a predictable world-writable path invites symlink races.
        assert str(path).startswith(str(Path.home()))


class TestPathSafety:
    """run_id and inventory_hostname end up in a path, so they cannot be
    allowed to walk out of the lease directory."""

    @pytest.mark.parametrize("module", [acquire, release])
    @pytest.mark.parametrize("bad", ["../../etc", "..", ".", "a/b", "with space", ""])
    def test_a_traversing_run_id_is_refused(self, module, bad):
        with pytest.raises(AnsibleActionFail, match="run_id"):
            module.safe_run_id(bad)

    @pytest.mark.parametrize("module", [acquire, release])
    def test_ordinary_run_ids_pass(self, module):
        assert module.safe_run_id("ci-run_2.1") == "ci-run_2.1"

    @pytest.mark.parametrize("module", [acquire, release])
    @pytest.mark.parametrize("bad", ["../evil", "a/b", ".", ".."])
    def test_a_traversing_hostname_is_refused(self, module, bad):
        with pytest.raises(AnsibleActionFail, match="lease file name"):
            module.lease_filename(bad)

    @pytest.mark.parametrize("module", [acquire, release])
    def test_hostnames_a_filesystem_accepts_are_kept_verbatim(self, module):
        # Kubespray inventories routinely name hosts by address.
        assert module.lease_filename("node-1.example.com") == "node-1.example.com.lease"
        assert module.lease_filename("fd00::1") == "fd00::1.lease"

    def test_both_plugins_agree_on_the_lease_file_name(self):
        assert acquire.lease_filename("n1") == release.lease_filename("n1")


class TestToBool:
    @pytest.mark.parametrize("value", [True, "true", "True", "yes", "on", "1", "y", "t"])
    def test_truthy(self, value):
        assert acquire.to_bool(value, "flag") is True
        assert release.to_bool(value, "flag") is True

    @pytest.mark.parametrize("value", [False, "false", "no", "off", "0", "n", "f"])
    def test_falsy(self, value):
        assert acquire.to_bool(value, "flag") is False
        assert release.to_bool(value, "flag") is False

    def test_unset_uses_the_default(self):
        assert acquire.to_bool(None, "flag", default=True) is True
        assert release.to_bool(None, "flag", default=False) is False

    @pytest.mark.parametrize("value", ["ture", "", "maybe", []])
    def test_ambiguous_input_is_an_error_rather_than_false(self, value):
        # abort_on_failure defaults to true: silently reading a typo as false
        # would disable the safety net without a word.
        with pytest.raises(AnsibleActionFail, match="must be a boolean"):
            acquire.to_bool(value, "abort_on_failure")


class TestAcquireAction:
    """End-to-end exercise of ActionModule.run() against a real directory."""

    def base_args(self, **overrides):
        args = {
            "concurrency": 2,
            "total_hosts": 6,
            "poll_interval": 1.0,
            "timeout": 60,
        }
        args.update(overrides)
        return args

    def run_acquire(self, args, hostname="n1", group_names=("kube_node",),
                    check_mode=False, **task_vars):
        action = make_action(acquire, "acquire_upgrade_slot", args, check_mode)
        task_vars.update({
            "inventory_hostname": hostname,
            "group_names": list(group_names),
        })
        return action.run(task_vars=task_vars)

    def test_rejects_unknown_parameters(self, lease_dir, forks):
        with pytest.raises(AnsibleActionFail, match="concurency"):
            self.run_acquire(self.base_args(concurency=2))

    def test_rejects_a_non_mapping_per_group(self, lease_dir, forks):
        with pytest.raises(AnsibleActionFail, match="must be a mapping"):
            self.run_acquire(self.base_args(per_group="kube_node: 2"))

    def test_check_mode_touches_nothing(self, lease_dir, forks):
        result = self.run_acquire(self.base_args(), check_mode=True)

        assert result["slot_acquired"] is True
        assert not lease_dir.exists()

    def test_acquires_a_free_slot(self, lease_dir, forks, clock):
        result = self.run_acquire(self.base_args())

        assert result["slot_acquired"] is True
        assert result["active_slots"] == 1
        assert result["concurrency"] == 2
        assert result["waited_seconds"] == 0.0
        assert (lease_dir / "n1.lease").exists()

    def test_the_lease_records_the_hosts_groups(self, lease_dir, forks, clock):
        self.run_acquire(self.base_args(), group_names=("kube_node", "calico_rr"))

        data = json.loads((lease_dir / "n1.lease").read_text())
        assert data["groups"] == ["calico_rr", "kube_node"]

    def test_waits_until_a_slot_is_freed(self, lease_dir, forks, clock):
        put_lease(lease_dir, "busy1")
        put_lease(lease_dir, "busy2")
        clock["on_sleep"] = lambda now: (
            (lease_dir / "busy1.lease").unlink() if now >= 3 else None
        )

        result = self.run_acquire(self.base_args())

        assert result["slot_acquired"] is True
        assert result["waited_seconds"] == 3.0

    def test_a_full_window_hits_the_timeout(self, lease_dir, forks, clock):
        put_lease(lease_dir, "busy1")
        put_lease(lease_dir, "busy2")

        with pytest.raises(AnsibleActionFail, match="waited 60s for a free slot"):
            self.run_acquire(self.base_args())

        assert not (lease_dir / "n1.lease").exists()

    def test_the_timeout_is_not_overshot_by_a_poll_interval(self, lease_dir, forks, clock):
        put_lease(lease_dir, "busy1")
        put_lease(lease_dir, "busy2")

        with pytest.raises(AnsibleActionFail, match="waited 7s"):
            self.run_acquire(self.base_args(timeout=7, poll_interval=2.0))

    def test_a_per_group_ceiling_defers_the_host(self, lease_dir, forks, clock):
        put_lease(lease_dir, "rr1", groups=["calico_rr"])

        with pytest.raises(AnsibleActionFail, match="waited"):
            self.run_acquire(
                self.base_args(per_group={"calico_rr": 1}), group_names=("calico_rr",),
            )

    def test_a_per_group_percentage_counts_the_group_not_the_play(
        self, lease_dir, forks, clock,
    ):
        # "50%" of two route reflectors is one, even though the play has six
        # hosts. rr1 already holds the only calico_rr slot.
        put_lease(lease_dir, "rr1", groups=["calico_rr"])

        with pytest.raises(AnsibleActionFail, match="waited"):
            self.run_acquire(
                self.base_args(concurrency=4, per_group={"calico_rr": "50%"}),
                hostname="rr2",
                group_names=("calico_rr",),
                ansible_play_hosts_all=["n1", "n2", "n3", "n4", "rr1", "rr2"],
                groups={"kube_node": ["n1", "n2", "n3", "n4"],
                        "calico_rr": ["rr1", "rr2"]},
            )

    def test_a_per_group_percentage_without_group_facts_is_an_error(
        self, lease_dir, forks, clock,
    ):
        with pytest.raises(AnsibleActionFail, match="no hosts in this play"):
            self.run_acquire(
                self.base_args(per_group={"calico_rr": "50%"}),
                group_names=("calico_rr",),
            )

    def test_the_clamp_warning_is_emitted_once_for_the_whole_run(
        self, lease_dir, forks, clock, monkeypatch,
    ):
        # Every worker resolves the same configuration; without warn_once the
        # operator would see this line once per node in the play.
        seen = []
        monkeypatch.setattr(acquire.display, "warning", seen.append)

        for host in ("n1", "n2", "n3"):
            self.run_acquire(self.base_args(concurrency=500), hostname=host)

        assert len(seen) == 1
        assert "capped at 19" in seen[0]

    def test_an_abandoned_lease_is_reclaimed(self, lease_dir, forks, clock):
        put_lease(lease_dir, "busy1")
        stale = put_lease(lease_dir, "killed", age=7200)

        result = self.run_acquire(self.base_args(lease_ttl=3600))

        assert result["slot_acquired"] is True
        assert not stale.exists()

    def test_a_host_never_waits_for_its_own_stale_lease(self, lease_dir, forks, clock):
        # A killed run sharing this run_id left our own lease behind. It is
        # deliberately exempt from the TTL sweep, so counting it towards the
        # window would make this host wait for itself until the timeout.
        mine = put_lease(lease_dir, "n1", age=7200)

        result = self.run_acquire(self.base_args(concurrency=1))

        assert result["slot_acquired"] is True
        assert result["active_slots"] == 1
        assert result["waited_seconds"] == 0.0
        # The lease is refreshed, so the TTL now counts from this attempt.
        assert json.loads(mine.read_text())["acquired_at"] > time.time() - 60

    def test_a_recorded_failure_stops_the_next_host(self, lease_dir, forks, clock):
        lease_dir.mkdir(parents=True)
        acquire.write_json_atomic(lease_dir / acquire.FAILURE_MARKER, {
            "host": "n2", "task": "Cordon and drain the node", "failed_at": 1.0,
        })

        with pytest.raises(AnsibleActionFail) as excinfo:
            self.run_acquire(self.base_args())

        assert "node n2 already failed" in str(excinfo.value)
        assert "Cordon and drain the node" in str(excinfo.value)
        assert not (lease_dir / "n1.lease").exists()

    def test_abort_on_failure_false_keeps_going(self, lease_dir, forks, clock):
        lease_dir.mkdir(parents=True)
        acquire.write_json_atomic(lease_dir / acquire.FAILURE_MARKER, {
            "host": "n2", "task": None, "failed_at": 1.0,
        })

        result = self.run_acquire(self.base_args(abort_on_failure=False))

        assert result["slot_acquired"] is True

    def test_a_single_fork_cannot_work(self, lease_dir, monkeypatch):
        from ansible import context

        monkeypatch.setattr(context, "CLIARGS", {"forks": 1}, raising=False)
        with pytest.raises(AnsibleActionFail, match="at least 2 forks"):
            self.run_acquire(self.base_args())


class TestReleaseAction:
    def run_release(self, args, hostname="n1", check_mode=False):
        action = make_action(release, "release_upgrade_slot", args, check_mode)
        return action.run(task_vars={"inventory_hostname": hostname})

    def test_releasing_without_a_lease_directory_is_not_an_error(self, lease_dir):
        result = self.run_release({})

        assert result["slot_released"] is False
        assert result["failure_recorded"] is False

    def test_releasing_a_held_slot(self, lease_dir):
        lease = put_lease(lease_dir, "n1")

        result = self.run_release({})

        assert result["slot_released"] is True
        assert not lease.exists()

    def test_releasing_a_slot_this_host_never_held(self, lease_dir):
        put_lease(lease_dir, "other")

        result = self.run_release({})

        assert result["slot_released"] is False
        assert (lease_dir / "other.lease").exists()

    def test_check_mode_touches_nothing(self, lease_dir):
        lease = put_lease(lease_dir, "n1")

        result = self.run_release({}, check_mode=True)

        assert result["slot_released"] is False
        assert lease.exists()

    def test_marking_a_failure_writes_the_marker(self, lease_dir):
        put_lease(lease_dir, "n1")

        result = self.run_release({
            "mark_failed": True,
            "task": "Fail after rescue",
            "reason": "Failed to drain node n1",
        })

        assert result["failure_recorded"] is True
        marker = acquire.read_failure_marker(lease_dir)
        assert marker["host"] == "n1"
        assert marker["task"] == "Fail after rescue"
        assert marker["reason"] == "Failed to drain node n1"
        # The two plugins have to agree end to end: this is what the next host
        # to reach acquire_upgrade_slot will be told.
        assert acquire.describe_failure(marker) == \
            " in task 'Fail after rescue': Failed to drain node n1"

    def test_a_marker_without_a_reason_stays_valid(self, lease_dir):
        put_lease(lease_dir, "n1")

        self.run_release({"mark_failed": True, "task": "Drain"})

        assert acquire.read_failure_marker(lease_dir)["reason"] is None

    def test_only_the_first_failure_is_recorded(self, lease_dir):
        put_lease(lease_dir, "n1")
        put_lease(lease_dir, "n2")
        self.run_release({"mark_failed": True, "task": "Drain"}, hostname="n1")

        result = self.run_release({"mark_failed": True, "task": "Other"}, hostname="n2")

        assert result["failure_recorded"] is False
        # The node that actually broke the run stays the one being reported.
        assert acquire.read_failure_marker(lease_dir)["host"] == "n1"

    def test_rejects_unknown_parameters(self, lease_dir):
        with pytest.raises(AnsibleActionFail, match="mark_faild"):
            self.run_release({"mark_faild": True})

    def test_rejects_an_ambiguous_mark_failed(self, lease_dir):
        with pytest.raises(AnsibleActionFail, match="must be a boolean"):
            self.run_release({"mark_failed": "ture"})
