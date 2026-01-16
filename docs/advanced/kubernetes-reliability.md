# Overview

Distributed system such as Kubernetes are designed to be resilient to the
failures.  More details about Kubernetes High-Availability (HA) may be found at
[Building High-Availability Clusters](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)

To have a simple view the most of the parts of HA will be skipped to describe
Kubelet<->Controller Manager communication only.

By default the normal behavior looks like:

1. Kubelet updates it status to apiserver periodically, as specified by
   `--node-status-update-frequency`. The default value is **10s**.

2. Kubernetes controller manager checks the statuses of Kubelet every
   `–-node-monitor-period`. The default value is **5s**.

3. In case the status is updated within `--node-monitor-grace-period` of time,
   Kubernetes controller manager considers healthy status of Kubelet. The
   default value is **40s**.

> Kubernetes controller manager and Kubelet work asynchronously. It means that
> the delay may include any network latency, API Server latency, etcd latency,
> latency caused by load on one's control plane nodes and so on. So if
> `--node-status-update-frequency` is set to 5s in reality it may appear in
> etcd in 6-7 seconds or even longer when etcd cannot commit data to quorum
> nodes.

## Failure

Kubelet will try to make `nodeStatusUpdateRetry` post attempts. Currently
`nodeStatusUpdateRetry` is constantly set to 5 in
[kubelet.go](https://github.com/kubernetes/kubernetes/blob/release-1.5/pkg/kubelet/kubelet.go#L102).

Kubelet will try to update the status in
[tryUpdateNodeStatus](https://github.com/kubernetes/kubernetes/blob/release-1.5/pkg/kubelet/kubelet_node_status.go#L312)
function. Kubelet uses `http.Client()` Golang method, but has no specified
timeout. Thus there may be some glitches when API Server is overloaded while
TCP connection is established.

So, there will be `nodeStatusUpdateRetry` * `--node-status-update-frequency`
attempts to set a status of node.

At the same time Kubernetes controller manager will try to check
`nodeStatusUpdateRetry` times every `--node-monitor-period` of time. After
`--node-monitor-grace-period` it will consider node unhealthy.  Pods will then be rescheduled based on the
[Taint Based Eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/#taint-based-evictions)
timers that you set on them individually, or the API Server's global timers:`--default-not-ready-toleration-seconds` &
``--default-unreachable-toleration-seconds``.

Kube proxy has a watcher over API. Once pods are evicted, Kube proxy will
notice and will update iptables of the node. It will remove endpoints from
services so pods from failed node won't be accessible anymore.

## Recommendations for different cases

## Fast Update and Fast Reaction

If `--node-status-update-frequency` is set to **4s** (10s is default).
`--node-monitor-period` to **2s** (5s is default).
`--node-monitor-grace-period` to **20s** (40s is default).
`--default-not-ready-toleration-seconds` and ``--default-unreachable-toleration-seconds`` are set to **30**
(300 seconds is default).  Note these two values should be integers representing the number of seconds ("s" or "m" for
seconds\minutes are not specified).

In such scenario, pods will be evicted in **50s** because the node will be
considered as down after **20s**, and `--default-not-ready-toleration-seconds` or
``--default-unreachable-toleration-seconds`` occur after **30s** more.  However, this scenario creates an overhead on
etcd as every node will try to update its status every 2 seconds.

If the environment has 1000 nodes, there will be 15000 node updates per
minute which may require large etcd containers or even dedicated nodes for etcd.

> If we calculate the number of tries, the division will give 5, but in reality
> it will be from 3 to 5 with `nodeStatusUpdateRetry` attempts of each try. The
> total number of attempts will vary from 15 to 25 due to latency of all
> components.

## Medium Update and Average Reaction

Let's set `--node-status-update-frequency` to **20s**
`--node-monitor-grace-period` to **2m** and `--default-not-ready-toleration-seconds` and
``--default-unreachable-toleration-seconds`` to **60**.
In that case, Kubelet will try to update status every 20s. So, it will be 6 * 5
= 30 attempts before Kubernetes controller manager will consider unhealthy
status of node. After 1m it will evict all pods. The total time will be 3m
before eviction process.

Such scenario is good for medium environments as 1000 nodes will require 3000
etcd updates per minute.

> In reality, there will be from 4 to 6 node update tries. The total number of
> of attempts will vary from 20 to 30.

## Low Update and Slow reaction

Let's set `--node-status-update-frequency` to **1m**.
`--node-monitor-grace-period` will set to **5m** and `--default-not-ready-toleration-seconds` and
``--default-unreachable-toleration-seconds`` to **60**. In this scenario, every kubelet will try to update the status
every minute. There will be 5 * 5 = 25 attempts before unhealthy status. After 5m,
Kubernetes controller manager will set unhealthy status. This means that pods
will be evicted after 1m after being marked unhealthy. (6m in total).

> In reality, there will be from 3 to 5 tries. The total number of attempt will
> vary from 15 to 25.

There can be different combinations such as Fast Update with Slow reaction to
satisfy specific cases.
