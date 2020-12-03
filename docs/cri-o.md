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

## k8s-cluster/k8s-cluster.yml

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

[CRI-O]: https://cri-o.io/
