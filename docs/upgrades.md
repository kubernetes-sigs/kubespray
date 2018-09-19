Upgrading Kubernetes in Kubespray
=============================

#### Description

Kubespray handles upgrades the same way it handles initial deployment. That is to
say that each component is laid down in a fixed order. You should be able to
upgrade from Kubespray tag 2.0 up to the current master without difficulty. You can
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
ansible-playbook cluster.yml -i inventory/sample/hosts.ini -e kube_version=v1.4.3
```

And then repeat with v1.4.6 as kube_version:

```
ansible-playbook cluster.yml -i inventory/sample/hosts.ini -e kube_version=v1.4.6
```

#### Graceful upgrade

Kubespray also supports cordon, drain and uncordoning of nodes when performing
a cluster upgrade. There is a separate playbook used for this purpose. It is
important to note that upgrade-cluster.yml can only be used for upgrading an
existing cluster. That means there must be at least 1 kube-master already
deployed.

```
git fetch origin
git checkout origin/master
ansible-playbook upgrade-cluster.yml -b -i inventory/sample/hosts.ini -e kube_version=v1.6.0
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

#### Upgrade considerations

Kubespray supports rotating certificates used for etcd and Kubernetes
components, but some manual steps may be required. If you have a pod that
requires use of a service token and is deployed in a namespace other than
`kube-system`, you will need to manually delete the affected pods after
rotating certificates. This is because all service account tokens are dependent
on the apiserver token that is used to generate them. When the certificate
rotates, all service account tokens must be rotated as well. During the
kubernetes-apps/rotate_tokens role, only pods in kube-system are destroyed and
recreated. All other invalidated service account tokens are cleaned up
automatically, but other pods are not deleted out of an abundance of caution
for impact to user deployed pods.

### Component-based upgrades

A deployer may want to upgrade specific components in order to minimize risk
or save time. This strategy is not covered by CI as of this writing, so it is
not guaranteed to work.

These commands are useful only for upgrading fully-deployed, healthy, existing
hosts. This will definitely not work for undeployed or partially deployed
hosts.

Upgrade docker:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=docker
```

Upgrade etcd:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=etcd
```

Upgrade vault:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=vault
```

Upgrade kubelet:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=node --skip-tags=k8s-gen-certs,k8s-gen-tokens
```

Upgrade Kubernetes master components:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=master
```

Upgrade network plugins:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=network
```

Upgrade all add-ons:

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=apps
```

Upgrade just helm (assuming `helm_enabled` is true):

```
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=helm
```
