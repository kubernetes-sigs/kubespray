# Upgrade strategies

`upgrade-cluster.yml` walks through the worker nodes in one of two ways,
selected with `upgrade_strategy`.

| | `linear` (default) | `graceful_rolling` |
|---|---|---|
| Node selection | `serial:` batches | sliding window |
| A slow node holds up | the rest of its batch | nobody |
| Window size | `serial` | `upgrade_node_concurrency` |
| Per-group ceilings | no | yes |
| Stops on a failed node | `any_errors_fatal` | `upgrade_abort_on_failure` |
| Interactive `pause:` prompts | yes | no |

`linear` is unchanged and remains the default. Nothing in this document
applies unless you opt in.

## The problem with batches

With `serial: 20%` on a 20-node cluster, Ansible upgrades four nodes, waits for
all four, then starts the next four. One node that drains slowly - a large
StatefulSet, a `PodDisruptionBudget` that only releases a pod every few minutes -
holds the other three idle even though the cluster has capacity to keep going.

Worse, the batch is drained as a unit. If four nodes each host a replica of a
Deployment with `minAvailable: 3`, the API server refuses the fourth eviction
and the batch blocks until `drain_timeout` expires.

`graceful_rolling` replaces the batch with a window. Every node runs
independently; a node that finishes hands its slot to the next waiting node
immediately. With a window of 2 that same cluster never has more than two nodes
cordoned, and no node ever waits for a peer.

## When it actually helps

Not always, and it is worth knowing when not. With nodes that all take the same
time and nothing blocking eviction, a window of N and `serial: N` finish
together - the window can only start the next node once one has finished, which
is when the batch would have rotated anyway.

The difference appears in two situations. Measured on three worker nodes with a
window (and `serial`) of 2:

| Situation | `linear` | `graceful_rolling` |
|---|---|---|
| One node 150s slower than its peers | 471s | 369s (-22%) |
| `PodDisruptionBudget`, `minAvailable: 2` | drain fails after 591s | 394s |

The second row is not a speed difference. `serial: 2` drains both nodes of a
batch in lockstep: the first eviction is allowed, the second would breach the
budget, and the budget cannot recover because the first node may not uncordon
until the whole batch clears the drain task. Both nodes fail. The window
staggers the nodes instead, so the second drain starts after the first node is
already back - in that run it never hit the budget at all.

Uneven node durations are the common case in practice: a node hosting a large
StatefulSet, a slow disk, a `terminationGracePeriodSeconds` measured in
minutes.

## Enabling it

```yaml
# inventory/mycluster/group_vars/all/upgrade.yml
upgrade_strategy: graceful_rolling
upgrade_node_concurrency: 3
```

```console
ansible-playbook -i inventory/mycluster/hosts.yaml -f 10 upgrade-cluster.yml
```

**The fork count must exceed the window.** A node waiting for a slot occupies an
Ansible worker, so `upgrade_node_concurrency` is capped at `forks - 1` and you
will see a warning if your value is clamped. Ansible's default is 5 forks, which
allows a window of 4; pass `-f`, set `ANSIBLE_FORKS`, or put `forks` in the
`[defaults]` section of `ansible.cfg` to go wider. Forks above the window cost
almost nothing - the extra workers just sleep.

### Per-group ceilings

`upgrade_per_group_concurrency` constrains individual inventory groups on top of
the global window. A node starts only when every ceiling that applies to it has
room:

```yaml
upgrade_node_concurrency: 6
upgrade_per_group_concurrency:
  calico_rr: 1     # never take two route reflectors down together
  gpu_nodes: 2     # scarce hardware, drain gently
```

The key `default` covers nodes that are in none of the listed groups.

A percentage is taken of the group's own hosts in this play, not of the whole
cluster — `calico_rr: "50%"` means half of the route reflectors. `default` is
resolved against the nodes matching none of the other listed groups.

### All settings

| Variable | Default | Meaning |
|---|---|---|
| `upgrade_strategy` | `linear` | `linear` or `graceful_rolling`. |
| `upgrade_node_concurrency` | `"20%"` | Window size; integer or percentage of the play's hosts. Percentages round down with a floor of 1, exactly as `serial` does. Capped at `forks - 1`. |
| `upgrade_per_group_concurrency` | `{}` | Per-group ceilings; percentages count the group's own hosts. |
| `upgrade_abort_on_failure` | `true` | Stop draining further nodes once one has failed. |
| `upgrade_slot_poll_interval` | `5.0` | Seconds between checks while a node waits. |
| `upgrade_slot_lease_ttl` | `3600` | Age at which a slot is treated as abandoned and reclaimed. |
| `upgrade_slot_timeout` | `0` | Seconds a node may wait before failing; `0` waits indefinitely. |

## What you give up

ansible-core implements `any_errors_fatal` and `max_fail_percentage` only in the
`linear` strategy. Under `free` and `host_pinned` both are silently ignored -
the strategy prints a warning and carries on. Since `graceful_rolling` runs on
`host_pinned`, **`any_errors_fatal` has no effect on the worker play.**

`upgrade_abort_on_failure` (on by default) replaces it at the point that
matters: when a node fails, every node that has not yet been drained fails
immediately instead of starting. Nodes already inside the window finish their
upgrade rather than being abandoned mid-drain, which is what you want - a node
that is cordoned and drained should be brought back up.

Set `upgrade_abort_on_failure: false` if you would rather let the rollout
continue past a broken node.

Interactive prompts are rejected outright. `upgrade_node_confirm` and
`upgrade_node_post_upgrade_confirm` need `linear`: several nodes upgrade at
once, so their prompts would arrive interleaved on one terminal, and each
unanswered prompt pins a worker. The playbook fails early with this combination
rather than hanging.

There is a mechanical reason too. The `pause` module sets `BYPASS_HOST_LOOP`,
and `free`/`host_pinned` abort the whole run when they encounter such a task -
*before* evaluating its `when:`, so a false condition is no protection. The two
prompts therefore live in files that `upgrade/{pre,post}-upgrade` include
dynamically, which keeps them out of the play unless they are really wanted.

The timed waits are unaffected: `upgrade_node_pause_seconds` and
`upgrade_node_post_upgrade_pause_seconds` work under both strategies. They use
`wait_for`, which runs per host and does not bypass the host loop.

## Scope

Only the worker play uses the sliding window. The other plays stay `linear`,
deliberately:

- **Control plane** already runs `serial: 1`. A window of one is the same thing,
  and the play also installs cluster-wide addons that must run exactly once.
- **The calico / cloud-controller play** applies cluster-wide manifests and
  never cordons a node, so the window would add risk without removing a
  bottleneck.

This matters because `run_once` is not honoured outside the `linear` strategy -
`free` warns and then runs the task on *every* host. A `kubectl replace` on a
shared ConfigMap or a `kubectl delete pod -l k8s-app=kube-proxy` executed once
per node is a genuine outage.

`roles/kubernetes/kubeadm` contains exactly such tasks, the kube-proxy
kubeconfig rewrite. They sit behind `kubeadm_patch_kube_proxy`, which defaults
to **off**: a play has to ask for them, and only a linear play may. `cluster.yml`
and `scale.yml` opt in; the rolling worker play cannot and does not, and
`upgrade_cluster.yml` runs them once for the whole cluster in a separate linear
play afterwards. Defaulting to off means a play added later is safe until
someone deliberately makes it unsafe, rather than the other way round.

If you add roles to the worker play, check them for `run_once`, `delegate_to`
against a single control-plane node, and anything that mutates cluster-wide
state. Node-local work is safe; cluster-wide work is not.

## How it works

Two action plugins implement the window as a semaphore on the Ansible
controller. They are ordinary action plugins - a stable, public extension point,
unlike the custom strategy plugins that ansible-core
[deprecated in 2.19](https://github.com/ansible/ansible/issues/84725).

```text
acquire_upgrade_slot     first task in the block
  ├── another node already failed?  ─▶ fail fast, do not drain
  ├── reclaim leases older than upgrade_slot_lease_ttl
  ├── wait while active leases >= window, or a group ceiling is full
  └── write <ansible run tmpdir>/kubespray-upgrade/<node>.lease

     ... cordon, drain, upgrade, uncordon, flush handlers ...

release_upgrade_slot     always: section, so a failed node releases too
  ├── delete the lease, freeing the slot for the next node
  └── if the node failed, write the UPGRADE_FAILED marker
```

Leases live inside Ansible's own controller-side temporary directory
(`~/.ansible/tmp/ansible-local-<run>/`). That directory is created once per
invocation and removed when the run ends, so concurrent `ansible-playbook`
invocations never share slots and a finished run leaves nothing behind. It sits
under `$HOME` with mode 0700 rather than in `/tmp`, where a predictable path
would be open to races on a shared controller.

Mutual exclusion uses `flock(2)`, so the Ansible controller must be Linux or
macOS. Managed nodes are unaffected - the plugins never connect to them.

## Verifying the window

Watch the cordoned nodes during an upgrade - the count should never exceed
`upgrade_node_concurrency`:

```console
watch -n2 "kubectl get nodes | grep -c SchedulingDisabled"
```

Run with `-vv` to see each node acquire and release:

```text
acquire_upgrade_slot: node3 acquired a slot after 41.2s (2/2 in flight)
release_upgrade_slot: node1 released its slot
```
