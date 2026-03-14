# Graceful Rolling Upgrade Strategy Plugin

**Issue**: [#12929](https://github.com/kubernetes-sigs/kubespray/issues/12929)

User-facing documentation: [docs/operations/upgrade-strategies.md](../operations/upgrade-strategies.md)

## Problem

The current upgrade batch mechanism (`serial: 20%` in `playbooks/upgrade_cluster.yml`) uses
Ansible's `linear` strategy with synchronised batches: all hosts in a batch wait for every other
host in the same batch before the next batch starts.

This creates two concrete problems:

1. **Upgrade bottleneck** — A single slow node (e.g. long pod drain) blocks all other nodes in its
   batch from completing, even if they finished their own work long ago.
2. **PodDisruptionBudget deadlock** — If too many nodes drain simultaneously, the Kubernetes
   eviction API rejects eviction requests (PDB violation). With the current model, nodes that
   _could_ uncordon (to free up pod capacity) are stuck waiting for the batch, preventing other
   nodes from draining. With a sliding window a finished node uncordons immediately, making room
   for the next drain to succeed.

## Desired Behaviour

Given hosts `A B C D E` and `concurrency: 2`:

```text
A and B start upgrading (2 active).
A finishes → C starts immediately (B & C active; no waiting for batch to sync).
C finishes → D starts (B & D active).
B finishes (was slow) → E starts (D & E active).
D finishes.
E finishes.
```

This is a **sliding window** / **host-pinned** execution model — as opposed to Ansible's native
`serial` batch model where each window must fully complete before the next window opens.

## Solution: `graceful_rolling` Strategy Plugin

A custom Ansible strategy plugin that inherits from `host_pinned` and adds:

- A **global concurrency limit** (sliding window size) configurable per play via a play variable
- An optional **per-group concurrency limit** (e.g. `kube_control_plane: 1`, `kube_node: 10`)
- A **waiting queue**: hosts that exceed the limit wait until an active host finishes
- **Per-host handler flushing** (inherited from `host_pinned`) — node-local handlers such as
  `restart kubelet` or `restart containerd` fire immediately when that node finishes, not at the
  end of the play

## Architecture

### New files

| Path | Purpose |
|------|---------|
| `plugins/strategy/graceful_rolling.py` | Core strategy plugin (Python) |
| `tests/unit/plugins/strategy/test_graceful_rolling.py` | Unit tests |
| `roles/kubespray_defaults/defaults/main/upgrade.yml` | Default variables |

### Modified files

| Path | Change |
|------|--------|
| `ansible.cfg` | Add `strategy_plugins = ./plugins/strategy` |
| `meta/runtime.yml` | Declare the plugin for collection mode |
| `playbooks/upgrade_cluster.yml` | Replace `serial:` with `strategy: graceful_rolling` + vars in 4 plays |

## Plugin Design

### File: `plugins/strategy/graceful_rolling.py`

```text
class StrategyModule(host_pinned.StrategyModule):
    _active_hosts: dict[hostname → group_name]   # currently running hosts
    _waiting_queue: deque[hostname]              # hosts waiting for a free slot

    run():
        while tasks remain or hosts active:
            for each newly-free slot:
                pop next host from _waiting_queue
                check global_limit and per_group_limit
                if within limits → start host, add to _active_hosts
            execute one iteration
            for each finished host:
                remove from _active_hosts
                try to unblock next host from _waiting_queue
```

### Configuration via play variables

```yaml
# In the play that uses the strategy:
strategy: graceful_rolling
vars:
  graceful_rolling_concurrency: 5          # global sliding-window size (default: ansible_forks)
  graceful_rolling_per_group:              # optional, per Ansible group
    kube_control_plane: 1
    kube_node: 10
    default: 5                             # fallback for hosts not in a listed group
```

### Handler behaviour

Handlers are flushed **per-host** as soon as that host completes all its tasks (inherited from
`host_pinned`). This is correct for kubespray because all upgrade handlers are node-local (e.g.
`systemd daemon-reload`, `restart kubelet`, `restart containerd`).

## Playbook Integration

### `playbooks/upgrade_cluster.yml` — 4 plays changed

| Play | Before | After |
|------|--------|-------|
| Play 3 — Upgrade container engine on non-cluster nodes | `serial: "{{ serial \| default('20%') }}"` | `strategy: "{{ upgrade_strategy \| default('linear') }}"` |
| Play 5 — Control plane upgrade | `serial: 1` | `strategy: "{{ upgrade_strategy \| default('linear') }}"`, `graceful_rolling_concurrency: "{{ upgrade_control_plane_concurrency \| default(1) }}"` |
| Play 6 — Calico / network plugin upgrade | `serial: "{{ serial \| default('20%') }}"` | `strategy: "{{ upgrade_strategy \| default('linear') }}"` |
| Play 7 — Worker node upgrade | `serial: "{{ serial \| default('20%') }}"` | `strategy: "{{ upgrade_strategy \| default('linear') }}"` + per_group config |

**Control-plane concurrency is always `1` by default** — this preserves etcd/API-server quorum.

### New defaults: `roles/kubespray_defaults/defaults/main/upgrade.yml`

```yaml
upgrade_strategy: linear                   # default; opt-in to graceful_rolling
upgrade_control_plane_concurrency: 1      # must stay 1 to preserve etcd quorum
upgrade_node_concurrency: "20%"           # matches original serial: default('20%')
upgrade_non_cluster_concurrency: "20%"    # matches original serial: default('20%')
upgrade_network_concurrency: "20%"        # matches original serial: default('20%')
```

Accepts plain integers or percentage strings (e.g. `"20%"`); see
[docs/operations/upgrade-strategies.md](../operations/upgrade-strategies.md)
for details.

### Backward compatibility

Set `upgrade_strategy: linear` in your inventory to get the old `serial:`-based behaviour
without any code changes.

## Unit Test Cases (`tests/unit/plugins/strategy/test_graceful_rolling.py`)

| # | Test | Verifies |
|---|------|---------|
| 1 | Sliding window: A finishes → C starts before B | Core rolling logic |
| 2 | Global `graceful_rolling_concurrency` is respected | Never exceeds limit |
| 3 | `graceful_rolling_per_group` limits hold per group | Per-group logic |
| 4 | `any_errors_fatal: true` stops the queue | Error propagation |
| 5 | Drain rescue: failed drain uncordons, queue continues | block/rescue interaction |
| 6 | No config → defaults to `ansible_forks` concurrency | Safe defaults |

## Verification Steps

1. Plugin discovery: `ANSIBLE_STRATEGY_PLUGINS=./plugins/strategy ansible-doc -t strategy graceful_rolling`
2. Unit tests: `python -m pytest tests/unit/plugins/strategy/test_graceful_rolling.py -v`
3. Syntax check: `ansible-playbook --syntax-check playbooks/upgrade_cluster.yml`
4. Live upgrade monitoring: confirm `SchedulingDisabled` count never exceeds configured concurrency
5. Regression: `upgrade_strategy: linear` produces identical behaviour to `serial: 20%`

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Class inherits from `host_pinned` (not `free` directly) | `HostPinnedStrategyModule.__init__` sets `_host_pinned = True`, which gives the inner dispatch loop correct slot-break semantics. `FreeStrategyModule` has no such control. |
| `run()` is a fork of `free.StrategyModule.run()` | `HostPinnedStrategyModule` has no `run()` of its own — it relies on `FreeStrategyModule.run()` via MRO. Our `run()` is therefore a tracked copy of `free.run()`, extended with the sliding-window logic. The drift-detection script (`check_free_strategy_drift.py`) monitors this base for upstream changes. |
| Configure via play vars, not play-level YAML keywords | Avoids new YAML schema; vars are easily overridable from inventory |
| Control-plane default concurrency = 1 | Losing API-server quorum during upgrade is unacceptable |
| Per-host handler flushing | Node-local handlers should not wait for all nodes; inherited correctly from `host_pinned` |
| No community.general upstream (initially) | Reduces scope; collection-mode compatibility can be added later |
| Default strategy remains `linear` | Opt-in model; existing users are unaffected until they explicitly opt in |
| `ALLOW_BASE_THROTTLING = False` | Prevents double-counting: our `run()` loop implements throttle internally, identical to `free` |

---

## Prior Art

This plugin solves a problem that the Ansible community has wanted to address for a decade.
Understanding the prior art clarifies _why_ kubespray ships its own strategy rather than
reusing an existing one.

| Source | Summary | Why not used |
|--------|---------|-------------|
| [ansible/ansible#18390](https://github.com/ansible/ansible/issues/18390) (2016) | First request for a slot-based (Pogo-style) rolling strategy in Ansible core. bcoca clarified that `free + forks` does **not** solve it — `free` distributes tasks round-robin across all hosts, not per-host. | Closed without implementation; redirected to community.general. |
| [ansible/ansible#81736](https://github.com/ansible/ansible/issues/81736) (2023) | Request by **@VannTen**, explicitly motivated by `kubespray/playbooks/upgrade_cluster.yml`. Demonstrates that `throttle:` behaves task-locally, not play-locally. | Closed; no new plugins accepted in ansible-core since 2.10. |
| [ansible/ansible#81744](https://github.com/ansible/ansible/pull/81744) (2023) | `rolling_play` strategy PR by @VannTen. Built on `free` and misused `throttle:` as a play-level slot counter. Identified gap: no `"20%"` support in throttle. | Closed; misuse of `throttle:` is an anti-pattern (see upgrade-strategies.md). |
| [community.general#10920](https://github.com/ansible-collections/community.general/issues/10920) (2025) | Same request escalated to community.general by @VannTen. Still open. Already links to our issue #12929. | No implementation yet in community.general. |

### Why `HostPinnedStrategyModule` as base class, but `free.run()` as implementation

All prior art attempts (including #81744) build on `free` directly. The two strategies
are related — `host_pinned` is a subclass of `free` — but differ in one critical point:

```text
FreeStrategyModule:         round-robin task dispatch across ALL hosts
                            → no per-host ordering guarantee
                            → no built-in concurrency cap
                            → defines run()

HostPinnedStrategyModule:   subclass of FreeStrategyModule
                            → sets _host_pinned = True in __init__
                            → _host_pinned causes the inner dispatch loop to break
                              when workers_free == 0  (slot semantics!)
                            → does NOT define its own run(); inherits free.run()
```

`graceful_rolling` therefore uses `HostPinnedStrategyModule` as its **class base** to
get `_host_pinned = True` for free — but its `run()` is a **fork of `free.run()`**,
because that is the actual base implementation in the MRO.  The added sliding-window
logic and per-group limits live entirely inside that forked `run()`.

This also explains why the drift-detection script targets `free.StrategyModule.run()`
and not `host_pinned.StrategyModule.run()`: if ansible-core ever changes the free loop,
our fork needs to be reviewed regardless of which class we inherit from.

---

## Ansible Version Compatibility

The plugin uses three ansible-core API surfaces that have version history:

| API | Introduced | Change history | Our code |
|-----|-----------|----------------|----------|
| `Templar(loader, variables=None)` | ≤ 2.17 had `shared_loader_obj` as second param | Removed in 2.18 — signature is now `Templar(loader, variables=None)` | `Templar(loader=self._loader, variables=play_vars)` — compatible with 2.18+ |
| `StrategyBase.ALLOW_BASE_THROTTLING` | 2.18 | Class-level bool; `True` by default. When `False`, `_queue_task()` skips its own throttle check. | We set `False` and implement throttle in `run()` to avoid double-counting. |
| `HostPinnedStrategyModule._host_pinned = True` | 2.18 | Set in `__init__`; causes the inner loop to break when `workers_free == 0`. | Inherited automatically. |
| `task.post_validate_attribute("name")` | 2.19 | New API for templating task names in the strategy loop. | **Not yet used.** In 2.18 `task.name` is templated by the callback layer. Comment at line 511–512. |

**Version pin in this repo:**

```yaml
# meta/runtime.yml
requires_ansible: ">=2.18.0,<2.19.0"

# requirements.txt
ansible==11.13.0   # ansible 11 ships ansible-core 2.18.x
```

### Why `<2.19.0` (upper bound)

The `run()` method in our plugin is a near-verbatim copy of `free.StrategyModule.run()` (see
`tests/scripts/check_free_strategy_drift.py`). Any upstream change to that method must be reviewed
before the upper bound is raised. The upper bound also prevents silent breakage when `task.name`
behavior changes in 2.19.

---

## Collection vs Repository Clone

Kubespray is primarily used by cloning the repository. The strategy plugin supports
both deployment modes:

### Repository clone (current default)

Ansible resolves `graceful_rolling` as a short name because `ansible.cfg` includes:

```ini
[defaults]
strategy_plugins = ./plugins/strategy
```

Users set:

```yaml
upgrade_strategy: graceful_rolling
```

### Ansible Collection install

When kubespray is installed as a collection (via a `requirements.yml` pointing to the
GitHub repository — see [docs/ansible/ansible_collection.md](../ansible/ansible_collection.md)),
the plugin is auto-discovered from `plugins/strategy/` and is available exclusively as its
Fully Qualified Collection Name (FQCN):

```yaml
upgrade_strategy: kubernetes_sigs.kubespray.graceful_rolling
```

Ansible does **not** automatically resolve short plugin names from installed collections.
The `strategy_plugins` path in a collection's own `ansible.cfg` has no effect after
a Galaxy install. No entry in `meta/runtime.yml` can create a short-name alias.

> Note: The playbook already supports FQCN transparently because all plays use
> `strategy: "{{ upgrade_strategy | default('linear') }}"`.
> No code change is needed; only the variable value differs between modes.

**When kubespray ships as a proper installable collection and `graceful_rolling` becomes the**
**recommended default, the `kubespray_defaults` role default for `upgrade_strategy` should**
**change from `linear` to `kubernetes_sigs.kubespray.graceful_rolling`.** This is a one-line
change in `roles/kubespray_defaults/defaults/main/upgrade.yml`.

---

## Maintainer Upgrade Checklist

Perform these steps whenever ansible-core (= `ansible` package) is bumped in `requirements.txt`.

### Step 1 — Update version bounds

```bash
# requirements.txt: update the ansible== pin
vim requirements.txt

# meta/runtime.yml: raise <X.Y.0 upper bound to match the new ansible-core minor
vim meta/runtime.yml

# playbooks/ansible_version.yml: update minimal_ansible_version / maximal_ansible_version
vim playbooks/ansible_version.yml
```

### Step 2 — Run drift detection

The `run()` method in our plugin is a selective copy of `free.StrategyModule.run()`. If
upstream changes that method, we must review and reconcile:

```bash
source .venv/bin/activate

# Check — exits 0 if unchanged, 1 if drift detected:
python tests/scripts/check_free_strategy_drift.py

# If drift is detected:
# 1. Read the diff in context:
git diff .venv/lib/python*/site-packages/ansible/plugins/strategy/free.py

# 2. Apply any relevant changes to plugins/strategy/graceful_rolling.py
# 3. Re-pin the hash:
python tests/scripts/check_free_strategy_drift.py --update
```

### Step 3 — Check version-specific APIs

For each entry in the compatibility table above:

| Check | Command |
|-------|---------|
| `Templar` signature | `python -c "from ansible.template import Templar; import inspect; print(inspect.signature(Templar.__init__))"` |
| `ALLOW_BASE_THROTTLING` | `python -c "from ansible.plugins.strategy import StrategyBase; print(StrategyBase.ALLOW_BASE_THROTTLING)"` |
| `_host_pinned` | `python -c "from ansible.plugins.strategy.host_pinned import StrategyModule; s = StrategyModule.__new__(StrategyModule); print(getattr(s, '_host_pinned', 'MISSING'))"` |
| `post_validate_attribute` | `python -c "from ansible.playbook.task import Task; print(hasattr(Task, 'post_validate_attribute'))"` |

If `post_validate_attribute` returns `True` (available in ansible-core 2.19+), replace the
task-name comment at `graceful_rolling.py:511–512` with the actual call:

```python
task.name = to_text(templar.template(task.post_validate_attribute("name"),
                    fail_on_undefined=False), nonstring='empty')
```

This mirrors the upstream `free.py` implementation.

### Step 4 — Run the full test suite

```bash
pytest tests/unit/plugins/strategy/test_graceful_rolling.py -v
ansible-playbook --syntax-check playbooks/upgrade_cluster.yml -i inventory/local/hosts.ini
```

### Step 5 — Update documentation

- `docs/operations/upgrade-strategies.md`: update the `Requires ansible-core X.Y.x` note
- `docs/developers/graceful-rolling-strategy.md` (this file): update the compatibility table
- Commit with message: `chore(strategy): bump ansible-core compat to X.Y`

---

## Contributing New Features

### Testing contract

Every code change to `plugins/strategy/graceful_rolling.py` must be accompanied by
corresponding unit tests. The test file is:
`tests/unit/plugins/strategy/test_graceful_rolling.py`

Test classes and their coverage:

| Class | What it covers |
|-------|----------------|
| `TestCanStartHost` | Per-group limit logic: global cap, group cap, default bucket, mixed groups |
| `TestRegisterHostFinish` | Counter decrements, sliding-window unblock, idempotency |
| `TestReadConcurrencyConfig` | Variable reading, Jinja2 templating, fork capping, percentage strings |
| `TestParseConcurrencyValue` | `_parse_concurrency_value()`: ints, percentages, edge cases |
| `TestClassConstants` | `_DEFAULT_BUCKET`, `_explicit_groups()` helper |

Run with: `pytest tests/unit/plugins/strategy/test_graceful_rolling.py -v`

### Adding a new configuration variable

1. Add the variable to `DOCUMENTATION.options` in `graceful_rolling.py`
2. Read it inside `_read_concurrency_config()` (or a dedicated helper)
3. Add a default to `roles/kubespray_defaults/defaults/main/upgrade.yml` with a comment
4. Thread the variable from `playbooks/upgrade_cluster.yml` into the relevant play `vars:`
5. Write unit tests in `TestReadConcurrencyConfig` or a new class
6. Document the variable in `docs/operations/upgrade-strategies.md`

### Modifying the `run()` loop

The `run()` method is deliberately kept structurally close to `free.StrategyModule.run()`.
All kubespray-specific additions are marked with `# GR:` comments. When making changes:

- Keep `# GR:` markers accurate — they serve as a diff guide for the maintainer who next
  runs drift detection
- Do **not** add logic that makes the loop diverge further from upstream without a clear
  reason — every divergence increases the maintenance burden on the next version bump
- If an upstream improvement in `free.run()` would benefit our plugin (e.g. a bug fix),
  cherry-pick it and update the drift hash (`check_free_strategy_drift.py --update`)
