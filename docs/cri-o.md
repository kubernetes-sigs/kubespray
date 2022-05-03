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
etcd_deployment_type: host # optionally kubeadm
```

## k8s_cluster/k8s_cluster.yml

```yaml
container_manager: crio
```

## all/crio.yml

Enable docker hub registry mirrors

```yaml
crio_registries:
  - prefix: docker.io
    insecure: false
    blocked: false
    location: registry-1.docker.io
    unqualified: false
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

## Note about user namespaces

CRI-O has support for user namespaces. This feature is optional and can be enabled by setting the following two variables.

```yaml
crio_runtimes:
  - name: runc
    path: /usr/bin/runc
    type: oci
    root: /run/runc
    allowed_annotations:
    - "io.kubernetes.cri-o.userns-mode"

crio_remap_enable: true
```

The `allowed_annotations` configures `crio.conf` accordingly.

The `crio_remap_enable` configures the `/etc/subuid` and `/etc/subgid` files to add an entry for the **containers** user.
By default, 16M uids and gids are reserved for user namespaces (256 pods * 65536 uids/gids) at the end of the uid/gid space.
