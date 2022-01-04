# containerd

[containerd] An industry-standard container runtime with an emphasis on simplicity, robustness and portability
Kubespray supports basic functionality for using containerd as the default container runtime in a cluster.

_To use the containerd container runtime set the following variables:_

## k8s_cluster.yml

When kube_node_ contains etcd, you define your etcd cluster to be as well schedulable for Kubernetes workloads. Thus containerd and dockerd can not run same time, must be set to bellow for running etcd cluster with only containerd.

```yaml
container_manager: containerd
```

## etcd.yml

```yaml
etcd_deployment_type: host
```

## Containerd config

Example: define registry mirror for docker hub

```yaml
containerd_registries:
  "docker.io":
    - "https://mirror.gcr.io"
    - "https://registry-1.docker.io"
```

[containerd]: https://containerd.io/
