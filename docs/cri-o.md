# CRI-O

[CRI-O] is a lightweight container runtime for Kubernetes.
Kubespray supports basic functionality for using CRI-O as the default container runtime in a cluster.

* Kubernetes supports CRI-O on v1.11.1 or later.
* etcd: configure either kubeadm managed etcd or host deployment

_To use the CRI-O container runtime set the following variables:_

## all/all.yml

```yaml
download_container: false
skip_downloads: false
etcd_kubeadm_enabled: true
```

## k8s_cluster/k8s_cluster.yml

```yaml
container_manager: crio
```

## etcd.yml

```yaml
etcd_deployment_type: host # optionally and mutually exclusive with etcd_kubeadm_enabled
```

## all/crio.yml

Enable docker hub registry mirrors

```yaml
crio_registries_mirrors:
  - prefix: docker.io
    insecure: false
    blocked: false
    location: registry-1.docker.io
    mirrors:
      - location: 192.168.100.100:5000
        insecure: true
      - location: mirror.gcr.io
        insecure: false
```

## Note about pids_limit

For heavily mult-threaded workloads like databases, the default of 1024 for pids-limit is too low.
This parameter controls not just the number of processes but also the amount of threads
(since a thread is technically a process with shared memory). See [cri-o#1921]

In order to increase the default `pids_limit` for cri-o based deployments you need to set the `crio_pids_limit`
for your `k8s_cluster` ansible group or per node depending on the use case.

```yaml
crio_pids_limit: 4096
```

[CRI-O]: https://cri-o.io/
[cri-o#1921]: https://github.com/cri-o/cri-o/issues/1921
