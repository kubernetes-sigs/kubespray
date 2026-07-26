# Sliding-window upgrades: design notes

How `upgrade_strategy: graceful_rolling` is built and, more usefully, which
ansible-core behaviours forced it into this shape. Read
[Upgrade strategies](/docs/operations/upgrade-strategies.md) first for what the
feature does; this document is for changing it.

All ansible-core references below are against **2.18.14**, which is what
`ansible==11.13.0` in `requirements.txt` currently resolves to. Re-check them
when that pin moves.

## Why not a strategy plugin

The obvious implementation is a custom strategy plugin, and
[PR #13080](https://github.com/kubernetes-sigs/kubespray/pull/13080) was exactly
that. It was closed because ansible-core
[deprecated custom strategy plugins](https://github.com/ansible/ansible/issues/84725)
with no replacement API announced. Only *custom* ones: the issue is explicit
that "the existing strategy plugins in ansible-core will remain".

That matters, because the built-in `host_pinned` already *is* a sliding window:

> Ansible will not wait for other hosts to finish the current task before
> queuing the next task for a host that has finished. Once a host is done with
> the play, it opens its slot to a new host that was waiting to start.

`host_pinned` (`ansible/plugins/strategy/host_pinned.py:43`) is `free` with
`_host_pinned = True`, which caps in-flight hosts at the fork count. So the
closed PR's 714-line fork of `free.StrategyModule.run()` existed for two
features only: a window narrower than `forks`, and per-group ceilings. Both fit
in action plugins, which are a supported, stable extension point.

## Architecture

```text
playbooks/upgrade_cluster.yml     worker play: strategy host_pinned, serial 100%
  └── block:
        acquire_upgrade_slot      blocks until a slot is free, writes a lease
        ... pre-upgrade → container-engine → node → kubeadm → post-upgrade ...
        meta: flush_handlers      services restart before the slot is handed on
        set_fact upgrade_slot_node_ok
      always:
        release_upgrade_slot      deletes the lease; marks failure if the fact is unset
```

`plugins/action/{acquire,release}_upgrade_slot.py` coordinate through a
directory of lease files on the controller, serialised with `fcntl.flock`. One
file per host holding a slot; a `UPGRADE_FAILED` marker file when a node has
failed.

`serial: 100%` puts every node in one batch so the strategy sees them all at
once; the window is then enforced by the semaphore rather than by `serial`,
which is what allows it to be narrower than `forks` and to vary per group.

## The four constraints that shaped this

Everything awkward in the implementation traces back to one of these. None are
kubespray's doing.

### 1. `run_once` is ignored outside `linear`

`free.py:172` warns and then runs the task **on every host**. There is no
opt-out.

This is why only the worker play is rolling. The control-plane play already runs
`serial: 1` (a window of one is the same thing) and installs cluster-wide
addons; the calico play applies cluster-wide manifests and never cordons a node,
so a window would add risk without removing a bottleneck.

It is also why `roles/kubernetes/kubeadm` was split. Its kube-proxy ConfigMap
rewrite and `kubectl delete pod -l k8s-app=kube-proxy` are cluster-scoped and
`run_once`. Under `free` that is N concurrent `kubectl replace` calls on one
object and N cluster-wide kube-proxy restarts. They now live in
`tasks/kube_proxy_kubeconfig.yml` behind `kubeadm_patch_kube_proxy`, which
**defaults to off** — a play must ask for them, and only a linear play may.
`cluster.yml` and `scale.yml` opt in; `upgrade_cluster.yml` runs them once in a
dedicated linear play after the window.

Deriving that flag from `upgrade_strategy` does not work: it is an
inventory-level setting, so `graceful_rolling` in `group_vars` would silently
disable the patch for ordinary `cluster.yml` runs. Ansible exposes no magic
variable for the running play's strategy (`ansible_play_name`,
`ansible_play_hosts`, `ansible_play_hosts_all`, `ansible_play_batch`,
`ansible_play_role_names` — that is the complete list), so the role cannot
detect its own context. Hence the fail-safe default instead.

### 2. `any_errors_fatal` and `max_fail_percentage` only exist in `linear`

They are implemented in `linear.py:328` and `linear.py:336`. `free.py:81` and
`free.py:194` only print a warning. The worker play sets
`any_errors_fatal: true`, and switching it to `host_pinned` silently drops that.

`upgrade_abort_on_failure` (default true) restores the intent where it matters:
`release_upgrade_slot` writes the failure marker, and every subsequent
`acquire_upgrade_slot` fails instead of granting a slot. Nodes already inside
the window finish rather than being abandoned mid-drain.

This is deliberately weaker than `any_errors_fatal` — it stops nodes from
*starting*, it cannot interrupt one already running.

### 3. `pause` aborts the play outright

`pause` sets `BYPASS_HOST_LOOP`, and `free.py:168` raises `AnsibleError` rather
than running it. The raise happens at dispatch, **before the task's `when:` is
evaluated**, so a false condition does not help and neither does asserting the
confirm flags are unset. Every rolling upgrade died the moment the worker play
reached `upgrade/pre-upgrade`.

The two prompts therefore live in `confirm_upgrade.yml` /
`confirm_uncordon.yml`, pulled in with `include_tasks` (dynamic, so they only
enter the play when actually wanted). The timed waits moved to `wait_for`, which
sleeps when given neither port nor path (`modules/wait_for.py:542`) and runs per
host.

`pause` and `add_host` are the only ansible-core action plugins with
`BYPASS_HOST_LOOP`. `add_host` appears in none of the roles the worker play
runs.

### 4. A waiting host occupies a worker

`acquire_upgrade_slot` blocks, and a blocked task holds its fork. The window is
therefore clamped to `forks - 1`, with a warning rather than a hard failure —
Ansible's default of 5 forks would otherwise turn the default `"20%"`
concurrency into an abort on any cluster above 25 nodes.

The fork count is read from `context.CLIARGS` first: `DEFAULT_FORKS` has **no
`cli:` mapping** in `config/base.yml`, so `-f/--forks` never reaches the
constant. Reading `C.DEFAULT_FORKS` alone makes `-f 20` invisible.

## Details worth knowing before changing something

**Lease location.** Inside Ansible's own per-run controller temp directory
(`~/.ansible/tmp/ansible-local-<run>/kubespray-upgrade/`). That directory is
created once per invocation, inherited by every worker across `fork()`, and
removed when the run ends — so slots are scoped to one run, concurrent
invocations never collide, and nothing is left behind. It also sits under
`$HOME` with mode 0700, unlike a predictable path in `/tmp`. `os.getpgid(0)` is
only a fallback; two playbooks started from one non-interactive shell script
share a process group.

**`flock`** means the controller must be Linux or macOS. Managed nodes are
unaffected — the plugins set `_requires_connection = False` and never open a
connection.

**Handler ordering is already correct.** `Play.compile()`
(`playbook/play.py:292`) inserts an implicit `flush_handlers` block between the
roles/tasks section and `post_tasks`. The explicit `meta: flush_handlers` at the
end of the block is belt-and-braces: it guarantees kubelet and the container
runtime have restarted before the slot is handed to the next node.

**`block`/`always`, deliberately no `rescue`.** A `rescue` would change what
happens under `linear`, which is the default and must stay untouched. Instead
the last task in the block sets `upgrade_slot_node_ok`, and `always` passes
`mark_failed: "{{ not (upgrade_slot_node_ok | default(false)) }}"`. Its absence
*is* the failure signal. This also means `ansible_failed_task` is unavailable,
which is why the abort message names the failing node but not the task.

**`roles:` became `tasks:` + `import_role`** because `always:` needs a block.
Checked before doing it: the worker play's roles keep their defaults to
themselves — nothing in it reads a sibling role's `defaults/`. `import_role` is
static, so tags propagate exactly as the `roles:` shorthand did.

## Testing

`tests/unit/plugins/action/test_upgrade_slots.py` covers the parts that are pure
functions: percentage resolution and clamping, per-group ceilings and the
default bucket, the lease lifecycle including abandoned-lease reclaim, and the
fork-count lookup. Run with `python -m pytest tests/unit`; wired into
`.pre-commit-config.yaml`.

The CI job `ubuntu24-calico-graceful-rolling-upgrade` uses `mode: ha`. Not
`all-in-one` — that node is in both `kube_control_plane` and `kube_node`, so
`kube_node:calico_rr:!kube_control_plane` is empty and the rolling play would be
skipped without failing. `ha` gives one dedicated worker, enough to exercise the
plugins, the validation play, `host_pinned` and the pause path. It does **not**
exercise the window; that needs three workers (`mode: node-etcd-client` is the
only stock layout that provides them).

`system_upgrade: true` was verified separately, on a three-VM cluster with one
control-plane node and two workers, at a fixed Kubernetes version so that only
the system-upgrade path was under test. Both workers entered the window, ran
the `download` role **inside** the `host_pinned` play (290 tasks), rebooted
(`"rebooted": true`), and released their slots — leases live on the controller,
so a managed-node reboot does not lose one. The three `run_once: true` tasks in
`download/tasks/prep_download.yml` executed on zero hosts, held off by their own
`when` guards; the `run_once` warning the strategy prints at dispatch is
therefore cosmetic here. The combinations that are *not* safe are rejected by
the validation play before anything runs.

Measured on six VMs, three workers, window and `serial` both 2:

| Situation | `linear` | `graceful_rolling` |
|---|---|---|
| Uniform nodes | same | same |
| One node 150s slower | 471s | 369s |
| PDB `minAvailable: 2` | drain fails after 591s | 394s |

The uniform row is not a disappointment, it is arithmetic: the window admits the
next node when one finishes, which is when a batch would have rotated anyway.

## Adding a role to the rolling play

Check it for:

- `run_once` — it will run on every node
- `pause` or any other `BYPASS_HOST_LOOP` action — it will abort the play
- `delegate_to` a single control-plane node combined with cluster-wide writes —
  correct per node, harmful when several nodes do it at once
- `any_errors_fatal` on a task — silently ignored

Node-local work is safe. Cluster-wide work belongs in a separate linear play.

## On an ansible-core bump

Re-verify, in order of how quietly they would break:

1. `free.py` still only *warns* about `run_once` rather than raising
2. `BYPASS_HOST_LOOP` is still limited to `pause` and `add_host`
3. `any_errors_fatal` is still absent from the free-family strategies (if it
   gains support, `upgrade_abort_on_failure` can be retired)
4. `DEFAULT_LOCAL_TMP` still names a per-run directory that is cleaned up
5. `DEFAULT_FORKS` still has no `cli:` mapping
