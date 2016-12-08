Upgrading Kubernetes in Kargo
=============================

#### Description

Kargo handles upgrades the same way it handles initial deployment. That is to
say that each component is laid down in a fixed order. You should be able to
upgrade from Kargo tag 2.0 up to the current master without difficulty. You can
also individually control versions of components by explicitly defining their
versions. Here are all version vars for each component:

* docker_version
* kube_version
* etcd_version
* calico_version
* calico_cni_version
* weave_version
* flannel_version
* kubedns_version

#### Example

If you wanted to upgrade just kube_version from v1.4.3 to v1.4.6, you could
deploy the following way:

```
ansible-playbook cluster.yml -i inventory/inventory.cfg -e kube_version=v1.4.3
```

And then repeat with v1.4.6 as kube_version:

```
ansible-playbook cluster.yml -i inventory/inventory.cfg -e kube_version=v1.4.6
```

#### Upgrade order

As mentioned above, components are upgraded in the order in which they were
installed in the Ansible playbook. The order of component installation is as
follows:

# Docker
# etcd
# kubelet and kube-proxy
# network_plugin (such as Calico or Weave)
# kube-apiserver, kube-scheduler, and kube-controller-manager
# Add-ons (such as KubeDNS)
