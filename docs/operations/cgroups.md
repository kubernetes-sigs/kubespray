# cgroups

To avoid resource contention between containers and host daemons in Kubernetes,
the kubelet components can use cgroups to limit resource usage.

## Node Allocatable

Node Allocatable is calculated by subtracting from the node capacity:

- kube-reserved reservations
- system-reserved reservations
- hard eviction thresholds

You can set those reservations:

```yaml
kube_memory_reserved: 256Mi
kube_cpu_reserved: 100m
kube_ephemeral_storage_reserved: 2Gi
kube_pid_reserved: "1000"

# System daemons (sshd, network manager, ...)
system_memory_reserved: 512Mi
system_cpu_reserved: 500m
system_ephemeral_storage_reserved: 2Gi
system_pid_reserved: "1000"
```

By default, the kubelet will enforce Node Allocatable for pods, which means
pods will be evicted when resource usage excess Allocatable.

You can optionnaly enforce the reservations for kube-reserved and
system-reserved, but proceed with caution (see [the kubernetes
guidelines](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/#general-guidelines)).
Note that to enforce kube-reserved or system-reserved, `kube_reserved_cgroups`
or `system_reserved_cgroups` needs to be specified respectively.

```yaml
enforce_allocatable_pods: true # default
enforce_allocatable_kube_reserved: true
enforce_allocatable_system_reserved: true

# This is required if you want to enforce limits on the resource usage of these daemons.
# It is not required if you just want to make resource reservations (kube_memory_reserved, kube_cpu_reserved, etc.)
# DEPRECATED: those settings are deprecated and will be removed in an upcoming release
# It will no longer be a requirement to enforce resources limits on kube / system daemons
kube_reserved_cgroups_for_service_slice: kube.slice
kube_reserved_cgroups: "/{{ kube_reserved_cgroups_for_service_slice }}"

system_reserved_cgroups_for_service_slice: system.slice
system_reserved_cgroups: "/{{ system_reserved_cgroups_for_service_slice }}"
```

You can learn more in the [official kubernetes documentation](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/).
