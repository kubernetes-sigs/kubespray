cri-o
===============

cri-o is container developed by kubernetes project.
Currently, only basic function is supported for cri-o.

* cri-o is supported kubernetes 1.11.1 or later.
* helm and other feature may not be supported due to docker dependency.
* scale.yml and upgrade-cluster.yml are not supported.

helm and other feature may not be supported due to docker dependency.

Use cri-o instead of docker, set following variable:

#### all.yml

```
kubeadm_enabled: true
...
download_container: false
skip_downloads: false
```

#### k8s-cluster.yml

```
etcd_deployment_type: host
kubelet_deployment_type: host
container_manager: crio
```

