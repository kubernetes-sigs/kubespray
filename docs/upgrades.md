# Upgrading Kubernetes in Kubespray

Kubespray handles upgrades the same way it handles initial deployment. That is to
say that each component is laid down in a fixed order.

You can also individually control versions of components by explicitly defining their
versions. Here are all version vars for each component:

* docker_version
* kube_version
* etcd_version
* calico_version
* calico_cni_version
* weave_version
* flannel_version
* kubedns_version

:warning: [Attempting to upgrade from an older release straight to the latest release is unsupported and likely to break something](https://github.com/kubernetes-sigs/kubespray/issues/3849#issuecomment-451386515) :warning:

See [Multiple Upgrades](#multiple-upgrades) for how to upgrade from older releases to the latest release

## Unsafe upgrade example

If you wanted to upgrade just kube_version from v1.4.3 to v1.4.6, you could
deploy the following way:

```ShellSession
ansible-playbook cluster.yml -i inventory/sample/hosts.ini -e kube_version=v1.4.3 -e upgrade_cluster_setup=true
```

And then repeat with v1.4.6 as kube_version:

```ShellSession
ansible-playbook cluster.yml -i inventory/sample/hosts.ini -e kube_version=v1.4.6 -e upgrade_cluster_setup=true
```

The var ```-e upgrade_cluster_setup=true``` is needed to be set in order to migrate the deploys of e.g kube-apiserver inside the cluster immediately which is usually only done in the graceful upgrade. (Refer to [#4139](https://github.com/kubernetes-sigs/kubespray/issues/4139) and [#4736](https://github.com/kubernetes-sigs/kubespray/issues/4736))

## Graceful upgrade

Kubespray also supports cordon, drain and uncordoning of nodes when performing
a cluster upgrade. There is a separate playbook used for this purpose. It is
important to note that upgrade-cluster.yml can only be used for upgrading an
existing cluster. That means there must be at least 1 kube-master already
deployed.

```ShellSession
ansible-playbook upgrade-cluster.yml -b -i inventory/sample/hosts.ini -e kube_version=v1.6.0
```

After a successful upgrade, the Server Version should be updated:

```ShellSession
$ kubectl version
Client Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.0", GitCommit:"fff5156092b56e6bd60fff75aad4dc9de6b6ef37", GitTreeState:"clean", BuildDate:"2017-03-28T19:15:41Z", GoVersion:"go1.8", Compiler:"gc", Platform:"darwin/amd64"}
Server Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.0+coreos.0", GitCommit:"8031716957d697332f9234ddf85febb07ac6c3e3", GitTreeState:"clean", BuildDate:"2017-03-29T04:33:09Z", GoVersion:"go1.7.5", Compiler:"gc", Platform:"linux/amd64"}
```

## Multiple upgrades

:warning: [Do not skip releases when upgrading--upgrade by one tag at a time.](https://github.com/kubernetes-sigs/kubespray/issues/3849#issuecomment-451386515) :warning:

For instance, if you're on v2.6.0, then check out v2.7.0, run the upgrade, check out the next tag, and run the next upgrade, etc.

Assuming you don't explicitly define a kubernetes version in your k8s-cluster.yml, you simply check out the next tag and run the upgrade-cluster.yml playbook

* If you do define kubernetes version in your inventory (e.g. group_vars/k8s-cluster.yml) then either make sure to update it before running upgrade-cluster, or specify the new version you're upgrading to: `ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml -e kube_version=v1.11.3`

  Otherwise, the upgrade will leave your cluster at the same k8s version defined in your inventory vars.

The below example shows taking a cluster that was set up for v2.6.0 up to v2.10.0

```ShellSession
$ kubectl get node
NAME      STATUS    ROLES         AGE       VERSION
apollo    Ready     master,node   1h        v1.10.4
boomer    Ready     master,node   42m       v1.10.4
caprica   Ready     master,node   42m       v1.10.4

$ git describe --tags
v2.6.0

$ git tag
...
v2.6.0
v2.7.0
v2.8.0
v2.8.1
v2.8.2
...

$ git checkout v2.7.0
Previous HEAD position was 8b3ce6e4 bump upgrade tests to v2.5.0 commit (#3087)
HEAD is now at 05dabb7e Fix Bionic networking restart error #3430 (#3431)

# NOTE: May need to sudo pip3 install -r requirements.txt when upgrading.

ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml

...

$ kubectl get node
NAME      STATUS    ROLES         AGE       VERSION
apollo    Ready     master,node   1h        v1.11.3
boomer    Ready     master,node   1h        v1.11.3
caprica   Ready     master,node   1h        v1.11.3

$ git checkout v2.8.0
Previous HEAD position was 05dabb7e Fix Bionic networking restart error #3430 (#3431)
HEAD is now at 9051aa52 Fix ubuntu-contiv test failed (#3808)
```

:info: NOTE: Review changes between the sample inventory and your inventory when upgrading versions. :info:

Some deprecations between versions that mean you can't just upgrade straight from 2.7.0 to 2.8.0 if you started with the sample inventory.

In this case, I set "kubeadm_enabled" to false, knowing that it is deprecated and removed by 2.9.0, to delay converting the cluster to kubeadm as long as I could.

```ShellSession
$ ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml
...
    "msg": "DEPRECATION: non-kubeadm deployment is deprecated from v2.9. Will be removed in next release."
...
Are you sure you want to deploy cluster using the deprecated non-kubeadm mode. (output is hidden):
yes
...

$ kubectl get node
NAME      STATUS   ROLES         AGE    VERSION
apollo    Ready    master,node   114m   v1.12.3
boomer    Ready    master,node   114m   v1.12.3
caprica   Ready    master,node   114m   v1.12.3

$ git checkout v2.8.1
Previous HEAD position was 9051aa52 Fix ubuntu-contiv test failed (#3808)
HEAD is now at 2ac1c756 More Feature/2.8 backports for 2.8.1 (#3911)

$ ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml
...
    "msg": "DEPRECATION: non-kubeadm deployment is deprecated from v2.9. Will be removed in next release."
...
Are you sure you want to deploy cluster using the deprecated non-kubeadm mode. (output is hidden):
yes
...

$ kubectl get node
NAME      STATUS   ROLES         AGE     VERSION
apollo    Ready    master,node   2h36m   v1.12.4
boomer    Ready    master,node   2h36m   v1.12.4
caprica   Ready    master,node   2h36m   v1.12.4

$ git checkout v2.8.2
Previous HEAD position was 2ac1c756 More Feature/2.8 backports for 2.8.1 (#3911)
HEAD is now at 4167807f Upgrade to 1.12.5 (#4066)

$ ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml
...
    "msg": "DEPRECATION: non-kubeadm deployment is deprecated from v2.9. Will be removed in next release."
...
Are you sure you want to deploy cluster using the deprecated non-kubeadm mode. (output is hidden):
yes
...

$ kubectl get node
NAME      STATUS   ROLES         AGE    VERSION
apollo    Ready    master,node   3h3m   v1.12.5
boomer    Ready    master,node   3h3m   v1.12.5
caprica   Ready    master,node   3h3m   v1.12.5

$ git checkout v2.8.3
Previous HEAD position was 4167807f Upgrade to 1.12.5 (#4066)
HEAD is now at ea41fc5e backport cve-2019-5736 to release-2.8 (#4234)

$ ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml
...
    "msg": "DEPRECATION: non-kubeadm deployment is deprecated from v2.9. Will be removed in next release."
...
Are you sure you want to deploy cluster using the deprecated non-kubeadm mode. (output is hidden):
yes
...

$ kubectl get node
NAME      STATUS   ROLES         AGE     VERSION
apollo    Ready    master,node   5h18m   v1.12.5
boomer    Ready    master,node   5h18m   v1.12.5
caprica   Ready    master,node   5h18m   v1.12.5

$ git checkout v2.8.4
Previous HEAD position was ea41fc5e backport cve-2019-5736 to release-2.8 (#4234)
HEAD is now at 3901480b go to k8s 1.12.7 (#4400)

$ ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml
...
    "msg": "DEPRECATION: non-kubeadm deployment is deprecated from v2.9. Will be removed in next release."
...
Are you sure you want to deploy cluster using the deprecated non-kubeadm mode. (output is hidden):
yes
...

$ kubectl get node
NAME      STATUS   ROLES         AGE     VERSION
apollo    Ready    master,node   5h37m   v1.12.7
boomer    Ready    master,node   5h37m   v1.12.7
caprica   Ready    master,node   5h37m   v1.12.7

$ git checkout v2.8.5
Previous HEAD position was 3901480b go to k8s 1.12.7 (#4400)
HEAD is now at 6f97687d Release 2.8 robust san handling (#4478)

$ ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml
...
    "msg": "DEPRECATION: non-kubeadm deployment is deprecated from v2.9. Will be removed in next release."
...
Are you sure you want to deploy cluster using the deprecated non-kubeadm mode. (output is hidden):
yes
...

$ kubectl get node
NAME      STATUS   ROLES         AGE     VERSION
apollo    Ready    master,node   5h45m   v1.12.7
boomer    Ready    master,node   5h45m   v1.12.7
caprica   Ready    master,node   5h45m   v1.12.7

$ git checkout v2.9.0
Previous HEAD position was 6f97687d Release 2.8 robust san handling (#4478)
HEAD is now at a4e65c7c Upgrade to Ansible >2.7.0 (#4471)
```

:warning: IMPORTANT: Some of the variable formats changed in the k8s-cluster.yml between 2.8.5 and 2.9.0 :warning:

If you do not keep your inventory copy up to date, **your upgrade will fail** and your first master will be left non-functional until fixed and re-run.

It is at this point the cluster was upgraded from non-kubeadm to kubeadm as per the deprecation warning.

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml

...

$ kubectl get node
NAME      STATUS   ROLES         AGE     VERSION
apollo    Ready    master,node   6h54m   v1.13.5
boomer    Ready    master,node   6h55m   v1.13.5
caprica   Ready    master,node   6h54m   v1.13.5

# Watch out: 2.10.0 is hiding between 2.1.2 and 2.2.0

$ git tag
...
v2.1.0
v2.1.1
v2.1.2
v2.10.0
v2.2.0
...

$ git checkout v2.10.0
Previous HEAD position was a4e65c7c Upgrade to Ansible >2.7.0 (#4471)
HEAD is now at dcd9c950 Add etcd role dependency on kube user to avoid etcd role failure when running scale.yml with a fresh node. (#3240) (#4479)

ansible-playbook -i inventory/mycluster/hosts.ini -b upgrade-cluster.yml

...

$ kubectl get node
NAME      STATUS   ROLES         AGE     VERSION
apollo    Ready    master,node   7h40m   v1.14.1
boomer    Ready    master,node   7h40m   v1.14.1
caprica   Ready    master,node   7h40m   v1.14.1


```

## Upgrade order

As mentioned above, components are upgraded in the order in which they were
installed in the Ansible playbook. The order of component installation is as
follows:

* Docker
* etcd
* kubelet and kube-proxy
* network_plugin (such as Calico or Weave)
* kube-apiserver, kube-scheduler, and kube-controller-manager
* Add-ons (such as KubeDNS)

## Upgrade considerations

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

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=docker
```

Upgrade etcd:

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=etcd
```

Upgrade vault:

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=vault
```

Upgrade kubelet:

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=node --skip-tags=k8s-gen-certs,k8s-gen-tokens
```

Upgrade Kubernetes master components:

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=master
```

Upgrade network plugins:

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=network
```

Upgrade all add-ons:

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=apps
```

Upgrade just helm (assuming `helm_enabled` is true):

```ShellSession
ansible-playbook -b -i inventory/sample/hosts.ini cluster.yml --tags=helm
```
