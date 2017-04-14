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

#### Unsafe upgrade example

If you wanted to upgrade just kube_version from v1.4.3 to v1.4.6, you could
deploy the following way:

```
ansible-playbook cluster.yml -i inventory/inventory.cfg -e kube_version=v1.4.3
```

And then repeat with v1.4.6 as kube_version:

```
ansible-playbook cluster.yml -i inventory/inventory.cfg -e kube_version=v1.4.6
```

#### Graceful upgrade

Kargo also supports cordon, drain and uncordoning of nodes when performing 
a cluster upgrade. There is a separate playbook used for this purpose. It is
important to note that upgrade-cluster.yml can only be used for upgrading an
existing cluster. That means there must be at least 1 kube-master already
deployed.

```
git fetch origin
git checkout origin/master
ansible-playbook upgrade-cluster.yml -b -i inventory/inventory.cfg -e kube_version=v1.6.0
```

After a successul upgrade, the Server Version should be updated:

```
$ kubectl version
Client Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.0", GitCommit:"fff5156092b56e6bd60fff75aad4dc9de6b6ef37", GitTreeState:"clean", BuildDate:"2017-03-28T19:15:41Z", GoVersion:"go1.8", Compiler:"gc", Platform:"darwin/amd64"}
Server Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.0+coreos.0", GitCommit:"8031716957d697332f9234ddf85febb07ac6c3e3", GitTreeState:"clean", BuildDate:"2017-03-29T04:33:09Z", GoVersion:"go1.7.5", Compiler:"gc", Platform:"linux/amd64"}
```

#### Upgrade order

As mentioned above, components are upgraded in the order in which they were
installed in the Ansible playbook. The order of component installation is as
follows:

* Docker
* etcd
* kubelet and kube-proxy
* network_plugin (such as Calico or Weave)
* kube-apiserver, kube-scheduler, and kube-controller-manager
* Add-ons (such as KubeDNS)
