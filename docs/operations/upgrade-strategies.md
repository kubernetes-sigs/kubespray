# Upgrade Strategies

Kubespray supports multiple Ansible execution strategies for rolling cluster
upgrades. The strategy controls **how many nodes are upgraded concurrently** and
**when the next node is allowed to start**.

## Overview

| Strategy | Concurrency model | Batch synchronisation | PDB-deadlock risk | Availability |
|---|---|---|---|---|
| `linear` | Fixed batches via `serial:` | Yes — entire batch must finish before next starts | Yes (see below) | All kubespray versions |
| `graceful_rolling` | Sliding window via `graceful_rolling_concurrency` | No — a free slot opens as soon as one node finishes | No | kubespray ≥ 2.28 |

---

## `linear` (default)

The default Ansible strategy. Nodes are grouped into batches whose size is
controlled by `upgrade_node_concurrency` (default: `"20%"`). All nodes in a batch
must complete their tasks before the next batch starts.

```
Batch 1: [node1, node2, node3]  ──────────────────────────────────►  all done
Batch 2: [node4, node5, node6]                                     ──────────────────────────────►  all done
                                                                  ↑
                                                            synchronisation point:
                                                            batch 2 cannot start until batch 1 is fully done
```

**When to use:**
- You want maximum predictability and battle-tested behaviour.
- You are upgrading a small cluster where batch synchronisation is not a bottleneck.
- Your operations team is familiar with the classic `serial:` model.

**Known limitation — PodDisruptionBudget deadlock:**

Consider a deployment with `maxUnavailable: 1` spread across nodes and a batch
size of 2. Both nodes in the batch are drained simultaneously. The first drain
succeeds; rescheduled pods land on available nodes. The second drain triggers
an eviction that would exceed the PDB — `kubectl drain` blocks, waiting for the
first pod to become ready on its new node. But that pod needs a node that is
still cordoned (in the same batch). Result: a deadlock that requires manual
intervention.

```
Batch: [node1 (draining), node2 (draining)]
  node1 drain OK → pod rescheduled → tries to land on node3 (available)
  node2 drain BLOCKED → PDB violated (maxUnavailable: 1 already used)
  node3 is in batch 2 → not yet started → pod cannot be scheduled elsewhere
  → DEADLOCK
```

---

## `graceful_rolling` (opt-in)

A custom Ansible strategy plugin shipped with kubespray. Rather than grouping
nodes into fixed batches, it maintains a **sliding window**: as soon as one
node finishes its upgrade the next waiting node is immediately allowed to start,
up to the configured concurrency limit.

```
Window size: 2

t=0  node1 ══════════════════════╗
     node2 ═════════════╗        ║
t=1                     ╚► node3 ══════════════════╗
t=2                              ╚► node4 ══════════════╗
```

There is no synchronisation point between nodes. The strategy also supports
per-group concurrency limits, which is particularly useful for keeping
control-plane upgrades serial while allowing nodes to run at a higher
concurrency:

```yaml
# upgrade_cluster.yml (excerpt — set automatically by kubespray)
vars:
  graceful_rolling_concurrency: 5       # max. 5 nodes running in parallel
  graceful_rolling_per_group:
    kube_control_plane: 1               # etcd quorum: keep serial when etcd runs on control-plane nodes
    kube_node: 5                        # workers: up to 5 in parallel
```

**How PDB deadlocks are avoided:**

With `graceful_rolling` node1 finishes its drain and becomes available as a
scheduling target *before* node2 starts its drain. The rescheduled pod can land
on node1 immediately, the PDB budget is replenished, and node2's eviction
succeeds without blocking.

**When to use:**
- You have large worker pools (≥ 10 nodes) where batch synchronisation noticeably
  slows down upgrades.
- Your cluster runs stateful workloads with strict `PodDisruptionBudget` policies.
- You want faster upgrades without sacrificing the cordon/drain/uncordon safety
  guarantees.

**Known limitations:**
- `run_once` tasks execute without strict ordering guarantees relative to other
  hosts (identical behaviour to the Ansible `free` strategy; all `run_once`
  usages in kubespray are `delegate_to`-based and unaffected in practice).
- `any_errors_fatal` and `max_fail_percentage` emit a warning; tasks continue
  on all other hosts when one host fails (same as `free`).
- Requires ansible-core 2.18. x.

**`throttle:` — task-level secondary constraint:**

The standard Ansible `throttle:` keyword works with this strategy. It limits
how many workers may execute the _same task_ simultaneously, independently of
`graceful_rolling_concurrency`. The two constraints are applied side by side:

```yaml
# Example: limit a heavy download task to 3 simultaneous executions
# even when graceful_rolling_concurrency is 10.
- name: Pull container images
  command: crictl pull ...
  throttle: 3
```

This is a useful secondary knob when a specific task is I/O- or
bandwidth-bound (e.g. pulling large images from an internal registry).
Note that `graceful_rolling_concurrency` operates at the **play level**
(max concurrent hosts in the whole play), while `throttle:` operates at the
**task level** (max concurrent executions of one specific task).

---

## Usage

### Switching to `graceful_rolling` (opt-in)

Pass the variable on the command line:

```shell
ansible-playbook playbooks/upgrade_cluster.yml \
  -i inventory/mycluster/hosts.ini \
  -b \
  -e kube_version=1.35.1 \
  -e upgrade_strategy=graceful_rolling
```

Or set it permanently in your inventory group variables:

```yaml
# inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml
upgrade_strategy: graceful_rolling
```

### Concurrency tuning

| Variable | Default | Description |
|---|---|---|
| `upgrade_control_plane_concurrency` | `1` | Control-plane nodes upgraded simultaneously. Defaults to `1` because etcd is co-hosted on control-plane nodes by default and requires a quorum. If etcd is deployed standalone (not on control-plane nodes), this value can be increased — kube-apiserver, kube-controller-manager, and kube-scheduler do not require a quorum. |
| `upgrade_node_concurrency` | `"20%"` | Worker nodes upgraded simultaneously with `graceful_rolling`. Also the `serial:` batch size for `linear`. |
| `upgrade_network_concurrency` | `"20%"` | Nodes in the combined calico / cloud-controller upgrade play. |

All three variables accept a **plain integer or a percentage string**:

```yaml
# inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml

# Upgrade at most 20% of workers in parallel:
upgrade_node_concurrency: "20%"

# Or a fixed number:
upgrade_node_concurrency: 5
```

Percentages are resolved against the total number of hosts in the respective
play at the time the strategy initialises, rounded to the nearest integer,
and clamped to a minimum of 1.

### Per-group limits (graceful_rolling only)

```yaml
# Advanced: override per Ansible group within a single play
graceful_rolling_per_group:
  kube_control_plane: 1   # etcd quorum: keep serial when etcd runs on control-plane nodes
  kube_node: 3            # max 3 workers at once
  # Hosts not in any listed group fall through to graceful_rolling_concurrency
```

---

## Comparison at a glance

```
Cluster: 1 control-plane + 9 workers, upgrade_node_concurrency=3

linear (serial: 3)                                      graceful_rolling (concurrency=3)

[w1 w2 w3] ────────────►                                w1 ══════════════╗
                                                        w2 ═════════╗   ╚► w4 ════════╗
[w4 w5 w6]              ──────────────►                 w3 ══╗       ╚► w5 ════════╗    ╚► w7 ══════╗
                                                             ╚► w6 ════════╗       ╚► w8 ════╗      ╚► w9 ══╗
[w7 w8 w9]                              ──────────────►
           ↑                                                    ↑
  batch barriers                                              no barriers: next starts when slot opens
  slow nodes delay                                            slow nodes do not delay fast nodes
  the whole batch
```

With `linear`, one slow node in a batch holds up all subsequent batches.
With `graceful_rolling`, fast nodes immediately pull the next waiting node
forward, reducing total upgrade time for heterogeneous workloads.
