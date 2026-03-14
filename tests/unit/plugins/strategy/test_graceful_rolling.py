"""Unit tests for plugins/strategy/graceful_rolling.py

Tests are grouped by method:
  - TestHostGroupNames       : _host_group_names() static helper
  - TestCanStartHost         : per-group concurrency veto logic
  - TestRegisterHostStart    : per-group counter increment on host start
  - TestRegisterHostFinish   : per-group counter decrement + sliding-window test
  - TestReadConcurrencyConfig: play-var reading and clamping

Run with:
    python -m pytest tests/unit/plugins/strategy/test_graceful_rolling.py -v
"""
from __future__ import annotations

import importlib.util
import os
import unittest
from unittest.mock import MagicMock

# ── Ansible availability check ────────────────────────────────────────────────
_ANSIBLE_SKIP_REASON: str | None = None
try:
    import ansible  # noqa: F401 – imported only to check availability
except ImportError:
    _ANSIBLE_SKIP_REASON = (
        "ansible-core is not installed. Run: pip install -r requirements.txt"
    )

# ── Plugin loader ─────────────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
_PLUGIN_PATH = os.path.join(
    _REPO_ROOT, "plugins", "strategy", "graceful_rolling.py"
)


def _load_plugin():
    """Load graceful_rolling as a standalone module (no collection install)."""
    spec = importlib.util.spec_from_file_location("graceful_rolling", _PLUGIN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_strategy(mod, num_workers: int = 10):
    """Return a StrategyModule instance WITHOUT calling __init__.

    ``StrategyBase.__init__`` starts a background results-thread and reads
    ``ansible.context.CLIARGS``, both of which require a fully initialised
    Ansible environment.  For unit tests that only exercise the helper
    methods we bypass __init__ entirely and set only the attributes that
    those helpers actually access.
    """
    sm = object.__new__(mod.StrategyModule)
    # Attributes consumed by the helpers under test:
    sm._workers = [MagicMock() for _ in range(num_workers)]
    sm._variable_manager = MagicMock()
    sm._loader = MagicMock()
    return sm


# ── Tiny domain helpers ───────────────────────────────────────────────────────

def _make_group(name: str) -> MagicMock:
    g = MagicMock()
    g.name = name
    return g


def _make_host(name: str, *group_names: str) -> MagicMock:
    """Return a MagicMock that passes as an ansible.inventory.host.Host."""
    h = MagicMock()
    h.name = name
    h.get_name.return_value = name
    h.get_groups.return_value = (
        [_make_group("all")] + [_make_group(gn) for gn in group_names]
    )
    return h


# ── Tests ─────────────────────────────────────────────────────────────────────

@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestHostGroupNames(unittest.TestCase):
    """_host_group_names() strips the 'all' pseudo-group."""

    @classmethod
    def setUpClass(cls):
        cls.SM = _load_plugin().StrategyModule

    def test_single_group(self):
        host = _make_host("w1", "kube_node")
        self.assertEqual(self.SM._host_group_names(host), {"kube_node"})

    def test_multiple_groups(self):
        host = _make_host("cp-1", "kube_control_plane", "etcd")
        self.assertEqual(
            self.SM._host_group_names(host),
            {"kube_control_plane", "etcd"},
        )

    def test_only_all_group_returns_empty_set(self):
        host = _make_host("standalone")  # no explicit groups → only 'all'
        self.assertEqual(self.SM._host_group_names(host), set())


@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestCanStartHost(unittest.TestCase):
    """_can_start_host() enforces explicit-group and default limits."""

    @classmethod
    def setUpClass(cls):
        mod = _load_plugin()
        cls.strat = _make_strategy(mod)

    # ── No limits ────────────────────────────────────────────────────────

    def test_no_limits_always_allows(self):
        host = _make_host("h1", "kube_node")
        self.assertTrue(self.strat._can_start_host(host, {}, {}))

    # ── Explicit group limit ──────────────────────────────────────────────

    def test_under_limit_is_allowed(self):
        host = _make_host("w1", "kube_node")
        self.assertTrue(
            self.strat._can_start_host(host, {"kube_node": 2}, {"kube_node": 3})
        )

    def test_at_limit_is_denied(self):
        host = _make_host("w1", "kube_node")
        self.assertFalse(
            self.strat._can_start_host(host, {"kube_node": 3}, {"kube_node": 3})
        )

    def test_control_plane_limit_1_denied_when_full(self):
        host = _make_host("cp-1", "kube_control_plane")
        self.assertFalse(
            self.strat._can_start_host(
                host, {"kube_control_plane": 1}, {"kube_control_plane": 1}
            )
        )

    def test_control_plane_limit_1_allowed_when_slot_free(self):
        host = _make_host("cp-1", "kube_control_plane")
        self.assertTrue(
            self.strat._can_start_host(host, {}, {"kube_control_plane": 1})
        )

    # ── Default catch-all limit ───────────────────────────────────────────

    def test_default_limit_applies_to_unlisted_group(self):
        host = _make_host("mon-1", "monitoring")  # not in the explicit list
        self.assertFalse(
            self.strat._can_start_host(
                host,
                {"__default__": 2},
                {"kube_node": 5, "default": 2},
            )
        )

    def test_default_limit_not_applied_when_explicit_group_matches(self):
        # 'kube_node' is explicitly listed → default bucket is ignored for it.
        host = _make_host("w1", "kube_node")
        self.assertTrue(
            self.strat._can_start_host(
                host,
                {"__default__": 99},  # would block under default logic
                {"kube_node": 5, "default": 2},
            )
        )

    def test_default_limit_not_reached_is_allowed(self):
        host = _make_host("mon-1", "monitoring")
        self.assertTrue(
            self.strat._can_start_host(
                host,
                {"__default__": 1},
                {"default": 3},
            )
        )

    # ── Multi-group host ──────────────────────────────────────────────────

    def test_host_blocked_by_second_of_two_groups(self):
        host = _make_host("cp-1", "kube_control_plane", "etcd")
        # kube_control_plane has a free slot, but etcd is full
        self.assertFalse(
            self.strat._can_start_host(
                host,
                {"kube_control_plane": 0, "etcd": 2},
                {"kube_control_plane": 1, "etcd": 2},
            )
        )

    def test_host_allowed_when_both_groups_have_capacity(self):
        host = _make_host("cp-1", "kube_control_plane", "etcd")
        self.assertTrue(
            self.strat._can_start_host(
                host,
                {"etcd": 1},
                {"kube_control_plane": 1, "etcd": 2},
            )
        )


@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestRegisterHostStart(unittest.TestCase):
    """_register_host_start() increments the correct per-group counters."""

    @classmethod
    def setUpClass(cls):
        mod = _load_plugin()
        cls.strat = _make_strategy(mod)

    def test_adds_host_to_started_set(self):
        host = _make_host("w1", "kube_node")
        started, active = set(), {}
        self.strat._register_host_start(host, started, active, {"kube_node": 5})
        self.assertIn("w1", started)

    def test_increments_explicit_group_counter(self):
        host = _make_host("w1", "kube_node")
        started, active = set(), {}
        self.strat._register_host_start(host, started, active, {"kube_node": 5})
        self.assertEqual(active.get("kube_node"), 1)

    def test_counter_accumulates_across_multiple_starts(self):
        limits = {"kube_node": 5}
        started, active = set(), {}
        for i in range(3):
            host = _make_host(f"w{i}", "kube_node")
            self.strat._register_host_start(host, started, active, limits)
        self.assertEqual(active.get("kube_node"), 3)

    def test_idempotent_for_already_started_host(self):
        host = _make_host("w1", "kube_node")
        started = {"w1"}
        active = {"kube_node": 4}
        self.strat._register_host_start(host, started, active, {"kube_node": 5})
        self.assertEqual(active["kube_node"], 4)  # unchanged

    def test_increments_default_bucket_for_unlisted_group(self):
        host = _make_host("mon-1", "monitoring")
        started, active = set(), {}
        self.strat._register_host_start(
            host, started, active, {"kube_node": 5, "default": 2}
        )
        self.assertEqual(active.get("__default__"), 1)

    def test_no_limits_does_not_update_counters(self):
        host = _make_host("w1", "kube_node")
        started, active = set(), {}
        self.strat._register_host_start(host, started, active, {})
        self.assertIn("w1", started)
        self.assertEqual(active, {})  # counters stay empty when no limits


@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestRegisterHostFinish(unittest.TestCase):
    """_register_host_finish() decrements counters and unblocks next host."""

    @classmethod
    def setUpClass(cls):
        mod = _load_plugin()
        cls.strat = _make_strategy(mod)

    def _finish(self, host, started, active, finished, limits):
        """Helper: call _register_host_finish for a single host."""
        self.strat._register_host_finish(
            host.get_name(),
            {host.get_name(): host},
            finished,
            started,
            active,
            limits,
        )

    def test_adds_to_finished_set(self):
        host = _make_host("w1", "kube_node")
        started, active, finished = {"w1"}, {"kube_node": 1}, set()
        self._finish(host, started, active, finished, {"kube_node": 3})
        self.assertIn("w1", finished)

    def test_decrements_group_counter(self):
        host = _make_host("w1", "kube_node")
        started, active, finished = {"w1"}, {"kube_node": 3}, set()
        self._finish(host, started, active, finished, {"kube_node": 5})
        self.assertEqual(active["kube_node"], 2)

    def test_counter_clamps_at_zero(self):
        host = _make_host("w1", "kube_node")
        started, active, finished = {"w1"}, {"kube_node": 0}, set()
        self._finish(host, started, active, finished, {"kube_node": 5})
        self.assertEqual(active["kube_node"], 0)

    def test_idempotent_when_already_finished(self):
        host = _make_host("w1", "kube_node")
        started, active, finished = {"w1"}, {"kube_node": 2}, {"w1"}
        self._finish(host, started, active, finished, {"kube_node": 5})
        self.assertEqual(active["kube_node"], 2)  # unchanged

    def test_skipped_if_not_yet_started(self):
        # A host that never started (not in 'started') should be a no-op.
        host = _make_host("w1", "kube_node")
        started, active, finished = set(), {"kube_node": 2}, set()
        self._finish(host, started, active, finished, {"kube_node": 5})
        self.assertEqual(active["kube_node"], 2)
        self.assertNotIn("w1", finished)

    def test_sliding_window_core_behaviour(self):
        """Core rolling assertion from issue #12929.

        Scenario: concurrency=2, hosts A B C in kube_node.
        │ A and B are active (limit reached) → C is blocked.
        │ A finishes → its slot is freed.
        └ C may now start without waiting for B to finish.
        """
        limits = {"kube_node": 2}
        active = {"kube_node": 2}  # A and B both running
        started = {"A", "B"}
        finished = set()
        host_a = _make_host("A", "kube_node")
        host_b = _make_host("B", "kube_node")  # noqa: F841 – represents slow host
        host_c = _make_host("C", "kube_node")
        host_map = {"A": host_a, "B": host_b, "C": host_c}

        # C is blocked while both slots are taken.
        self.assertFalse(self.strat._can_start_host(host_c, active, limits))

        # A finishes — this is the "slot freed" event.
        self.strat._register_host_finish(
            "A", host_map, finished, started, active, limits
        )
        self.assertIn("A", finished)
        self.assertEqual(active["kube_node"], 1)

        # C can now start without B having to finish first.
        self.assertTrue(self.strat._can_start_host(host_c, active, limits))

        # Register C starting: B + C are now running.
        self.strat._register_host_start(host_c, started, active, limits)
        self.assertEqual(active["kube_node"], 2)  # B + C (A is gone)

    def test_pdb_unblock_scenario(self):
        """PodDisruptionBudget deadlock fix.

        control-plane: limit=1, kube_node: limit=3.
        cp-1 finishes → cp-2 can start; workers remain blocked at their limit.
        """
        limits = {"kube_control_plane": 1, "kube_node": 3}
        active = {"kube_control_plane": 1, "kube_node": 3}
        started = {"cp-1", "w1", "w2", "w3"}
        finished = set()
        cp1 = _make_host("cp-1", "kube_control_plane")
        cp2 = _make_host("cp-2", "kube_control_plane")
        w4 = _make_host("w4", "kube_node")
        host_map = {"cp-1": cp1, "cp-2": cp2}

        # cp-2 cannot start while cp-1 occupies the single slot.
        self.assertFalse(self.strat._can_start_host(cp2, active, limits))

        # cp-1 completes its upgrade.
        self.strat._register_host_finish(
            "cp-1", host_map, finished, started, active, limits
        )

        # cp-2 can now start.
        self.assertTrue(self.strat._can_start_host(cp2, active, limits))

        # Worker w4 is still blocked by the kube_node limit.
        self.assertFalse(self.strat._can_start_host(w4, active, limits))


@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestReadConcurrencyConfig(unittest.TestCase):
    """_read_concurrency_config() reads and templates play variables."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_plugin()

    def _make_sm(self, play_vars: dict, num_workers: int = 10):
        """Return a wired-up StrategyModule with play vars and a pass-through
        TemplateEngine mock (values are not Jinja2 expressions in these tests).
        """
        sm = _make_strategy(self.mod, num_workers)
        sm._variable_manager.get_vars.return_value = play_vars

        # Replace TemplateEngine in the module namespace with an identity stub.
        mock_te = MagicMock()
        mock_templar = MagicMock()
        mock_templar.template.side_effect = lambda x: x
        mock_te.return_value = mock_templar
        self.mod.TemplateEngine = mock_te

        return sm

    def _iterator(self):
        it = MagicMock()
        it._play = MagicMock()
        return it

    def test_defaults_to_fork_count_when_var_absent(self):
        sm = self._make_sm({}, num_workers=8)
        concurrency, per_group = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=50
        )
        self.assertEqual(concurrency, 8)
        self.assertEqual(per_group, {})

    def test_respects_concurrency_variable(self):
        sm = self._make_sm({"graceful_rolling_concurrency": 3})
        concurrency, _ = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=50
        )
        self.assertEqual(concurrency, 3)

    def test_concurrency_clamped_at_fork_count(self):
        # Requesting more workers than forks → capped at forks.
        sm = self._make_sm({"graceful_rolling_concurrency": 999}, num_workers=6)
        concurrency, _ = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=50
        )
        self.assertEqual(concurrency, 6)

    def test_per_group_limits_parsed_correctly(self):
        sm = self._make_sm(
            {
                "graceful_rolling_concurrency": 5,
                "graceful_rolling_per_group": {
                    "kube_control_plane": 1,
                    "kube_node": 8,
                },
            }
        )
        _, per_group = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=50
        )
        self.assertEqual(per_group, {"kube_control_plane": 1, "kube_node": 8})

    def test_concurrency_1_equivalent_to_serial_1(self):
        """concurrency=1 means at most one host active at a time (serial: 1)."""
        sm = self._make_sm({"graceful_rolling_concurrency": 1})
        concurrency, _ = sm._read_concurrency_config(
            self._iterator(), _make_host("cp-1"), total_hosts=50
        )
        self.assertEqual(concurrency, 1)

    def test_empty_per_group_returns_empty_dict(self):
        sm = self._make_sm({"graceful_rolling_per_group": {}})
        _, per_group = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=50
        )
        self.assertEqual(per_group, {})

    def test_percentage_string_resolved_against_total_hosts(self):
        """'20%' with 100 hosts resolves to concurrency=20."""
        sm = self._make_sm({"graceful_rolling_concurrency": "20%"}, num_workers=50)
        concurrency, _ = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=100
        )
        self.assertEqual(concurrency, 20)

    def test_percentage_string_clamped_at_fork_count(self):
        """100% with 200 hosts but only 10 forks → capped at 10."""
        sm = self._make_sm(
            {"graceful_rolling_concurrency": "100%"}, num_workers=10
        )
        concurrency, _ = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=200
        )
        self.assertEqual(concurrency, 10)

    def test_percentage_string_rounds_to_nearest_int(self):
        """33% with 10 hosts → round(3.3) = 3."""
        sm = self._make_sm({"graceful_rolling_concurrency": "33%"})
        concurrency, _ = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=10
        )
        self.assertEqual(concurrency, 3)

    def test_per_group_percentage_string_resolved(self):
        """Per-group values also accept percentage strings."""
        sm = self._make_sm(
            {
                "graceful_rolling_per_group": {
                    "kube_node": "20%",
                    "kube_control_plane": 1,
                }
            },
            num_workers=50,
        )
        _, per_group = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=10
        )
        self.assertEqual(per_group["kube_node"], 2)       # 20% of 10 = 2
        self.assertEqual(per_group["kube_control_plane"], 1)

    def test_per_group_percentage_clamped_to_min_1(self):
        """Per-group '1%' with 2 hosts → 0 → clamped to 1."""
        sm = self._make_sm(
            {"graceful_rolling_per_group": {"kube_node": "1%"}},
            num_workers=50,
        )
        _, per_group = sm._read_concurrency_config(
            self._iterator(), _make_host("h1"), total_hosts=2
        )
        self.assertEqual(per_group["kube_node"], 1)


@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestParseConcurrencyValue(unittest.TestCase):
    """_parse_concurrency_value() parses integers and percentage strings."""

    @classmethod
    def setUpClass(cls):
        mod = _load_plugin()
        cls.SM = mod.StrategyModule

    def test_plain_integer_unchanged(self):
        self.assertEqual(self.SM._parse_concurrency_value(5, total_hosts=100, max_workers=50), 5)

    def test_plain_integer_clamped_at_max(self):
        self.assertEqual(self.SM._parse_concurrency_value(999, total_hosts=100, max_workers=10), 10)

    def test_percentage_20_of_100_hosts(self):
        self.assertEqual(self.SM._parse_concurrency_value("20%", total_hosts=100, max_workers=50), 20)

    def test_percentage_50_of_6_hosts(self):
        """50% of 6 → round(3.0) = 3."""
        self.assertEqual(self.SM._parse_concurrency_value("50%", total_hosts=6, max_workers=50), 3)

    def test_percentage_rounds_up(self):
        """33% of 10 → round(3.3) = 3."""
        self.assertEqual(self.SM._parse_concurrency_value("33%", total_hosts=10, max_workers=50), 3)

    def test_percentage_rounds_half_up(self):
        """35% of 10 → round(3.5) = 4 (Python banker's rounding: round(3.5)=4)."""
        result = self.SM._parse_concurrency_value("35%", total_hosts=10, max_workers=50)
        self.assertIn(result, (3, 4))  # accept both rounding modes

    def test_percentage_minimum_is_1(self):
        """1% of 2 hosts → round(0.02)=0 → clamped to 1."""
        self.assertEqual(self.SM._parse_concurrency_value("1%", total_hosts=2, max_workers=50), 1)

    def test_percentage_with_whitespace(self):
        """Leading/trailing whitespace is stripped."""
        self.assertEqual(self.SM._parse_concurrency_value(" 50% ", total_hosts=10, max_workers=50), 5)

    def test_percentage_clamped_at_max_workers(self):
        """100% with 200 hosts but only 5 forks → capped at 5."""
        self.assertEqual(self.SM._parse_concurrency_value("100%", total_hosts=200, max_workers=5), 5)

    def test_string_integer_accepted(self):
        """A bare string integer (e.g. from Jinja2 template) is accepted."""
        self.assertEqual(self.SM._parse_concurrency_value("7", total_hosts=100, max_workers=50), 7)


@unittest.skipIf(_ANSIBLE_SKIP_REASON, _ANSIBLE_SKIP_REASON)
class TestClassConstants(unittest.TestCase):
    """Verify the class-level constants and helpers introduced for code clarity."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_plugin()
        cls.SM = cls.mod.StrategyModule

    def test_default_bucket_constant_exists(self):
        self.assertEqual(self.SM._DEFAULT_BUCKET, "__default__")

    def test_explicit_groups_strips_default_key(self):
        limits = {"kube_node": 3, "kube_control_plane": 1, "default": 2}
        result = self.SM._explicit_groups(limits)
        self.assertEqual(result, {"kube_node", "kube_control_plane"})

    def test_explicit_groups_empty_when_only_default(self):
        result = self.SM._explicit_groups({"default": 5})
        self.assertEqual(result, set())

    def test_explicit_groups_empty_limits(self):
        result = self.SM._explicit_groups({})
        self.assertEqual(result, set())

    def test_default_bucket_used_for_unlisted_host(self):
        """Hosts not in any explicit group are counted under _DEFAULT_BUCKET."""
        sm = _make_strategy(self.mod)
        host = _make_host("mon-1", "monitoring")
        started, active = set(), {}
        sm._register_host_start(
            host, started, active, {"kube_node": 5, "default": 2}
        )
        self.assertEqual(active.get(self.SM._DEFAULT_BUCKET), 1)
        self.assertEqual(active.get("monitoring"), None)


if __name__ == "__main__":
    unittest.main()
