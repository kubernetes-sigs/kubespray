containerd
===============

An industry-standard container runtime with an emphasis on simplicity,
robustness and portability
Currently, only basic function is supported for containerd.
Only tested on Ubuntu 18.04, will only work with Debian-based distros.

* containerd is supported kubernetes 1.11.1 or later.
* helm and other feature may not be supported due to docker dependency.
* scale.yml and upgrade-cluster.yml are not supported.

Use containerd instead of docker, set following variable:

#### all.yml

```
kubeadm_enabled: true
```

#### k8s-cluster.yml

```
etcd_deployment_type: host
container_manager: containerd
```

