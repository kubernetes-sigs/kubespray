# cgroups

To avoid the rivals for resources between containers or the impact on the host in Kubernetes, the kubelet components will rely on cgroups to limit the container’s resources usage.

## Enforcing Node Allocatable

You can use `kubelet_enforce_node_allocatable` to set node allocatable enforcement.

```yaml
# A comma separated list of levels of node allocatable enforcement to be enforced by kubelet.
kubelet_enforce_node_allocatable: "pods"
# kubelet_enforce_node_allocatable: "pods,kube-reserved"
# kubelet_enforce_node_allocatable: "pods,kube-reserved,system-reserved"
```

Note that to enforce kube-reserved or system-reserved, `kube_reserved_cgroups` or `system_reserved_cgroups` needs to be specified respectively.

Here is an example:

```yaml
kubelet_enforce_node_allocatable: "pods,kube-reserved,system-reserved"

# Reserve this space for kube resources
# Set to true to reserve resources for kube daemons
kube_reserved: true
kube_reserved_cgroups_for_service_slice: kube.slice
kube_reserved_cgroups: "/{{ kube_reserved_cgroups_for_service_slice }}"
kube_memory_reserved: 256Mi
kube_cpu_reserved: 100m
# kube_ephemeral_storage_reserved: 2Gi
# kube_pid_reserved: "1000"
# Reservation for master hosts
kube_master_memory_reserved: 512Mi
kube_master_cpu_reserved: 200m
# kube_master_ephemeral_storage_reserved: 2Gi
# kube_master_pid_reserved: "1000"

# Set to true to reserve resources for system daemons
system_reserved: true
system_reserved_cgroups_for_service_slice: system.slice
system_reserved_cgroups: "/{{ system_reserved_cgroups_for_service_slice }}"
system_memory_reserved: 512Mi
system_cpu_reserved: 500m
# system_ephemeral_storage_reserved: 2Gi
# system_pid_reserved: "1000"
# Reservation for master hosts
system_master_memory_reserved: 256Mi
system_master_cpu_reserved: 250m
# system_master_ephemeral_storage_reserved: 2Gi
# system_master_pid_reserved: "1000"
```

After the setup, the cgroups hierarchy is as follows:

```bash
/ (Cgroups Root)
├── kubepods.slice
│   ├── ...
│   ├── kubepods-besteffort.slice
│   ├── kubepods-burstable.slice
│   └── ...
├── kube.slice
│   ├── ...
│   ├── {{container_manager}}.service
│   ├── kubelet.service
│   └── ...
├── system.slice
│   └── ...
└── ...
```

You can learn more in the [official kubernetes documentation](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/).
