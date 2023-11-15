# Ansible

## Installing Ansible

Kubespray supports multiple ansible versions and ships different `requirements.txt` files for them.
Depending on your available python version you may be limited in choosing which ansible version to use.

It is recommended to deploy the ansible version used by kubespray into a python virtual environment.

```ShellSession
VENVDIR=kubespray-venv
KUBESPRAYDIR=kubespray
python3 -m venv $VENVDIR
source $VENVDIR/bin/activate
cd $KUBESPRAYDIR
pip install -U -r requirements.txt
```

In case you have a similar message when installing the requirements:

```ShellSession
ERROR: Could not find a version that satisfies the requirement ansible==7.6.0 (from -r requirements.txt (line 1)) (from versions: [...], 6.7.0)
ERROR: No matching distribution found for ansible==7.6.0 (from -r requirements.txt (line 1))
```

It means that the version of Python you are running is not compatible with the version of Ansible that Kubespray supports.
If the latest version supported according to pip is 6.7.0 it means you are running Python 3.8 or lower while you need at least Python 3.9 (see the table below).

### Ansible Python Compatibility

Based on the table below and the available python version for your ansible host you should choose the appropriate ansible version to use with kubespray.

| Ansible Version | Python Version |
|-----------------|----------------|
| >= 2.15.5       | 3.9-3.11       |

## Inventory

The inventory is composed of 3 groups:

* **kube_node** : list of kubernetes nodes where the pods will run.
* **kube_control_plane** : list of servers where kubernetes control plane components (apiserver, scheduler, controller) will run.
* **etcd**: list of servers to compose the etcd server. You should have at least 3 servers for failover purpose.

Note: do not modify the children of _k8s_cluster_, like putting
the _etcd_ group into the _k8s_cluster_, unless you are certain
to do that and you have it fully contained in the latter:

```ShellSession
etcd ⊂ k8s_cluster => kube_node ∩ etcd = etcd
```

When _kube_node_ contains _etcd_, you define your etcd cluster to be as well schedulable for Kubernetes workloads.
If you want it a standalone, make sure those groups do not intersect.
If you want the server to act both as control-plane and node, the server must be defined
on both groups _kube_control_plane_ and _kube_node_. If you want a standalone and
unschedulable control plane, the server must be defined only in the _kube_control_plane_ and
not _kube_node_.

There are also two special groups:

* **calico_rr** : explained for [advanced Calico networking cases](/docs/calico.md)
* **bastion** : configure a bastion host if your nodes are not directly reachable

Below is a complete inventory example:

```ini
## Configure 'ip' variable to bind kubernetes services on a
## different ip than the default iface
node1 ansible_host=95.54.0.12 ip=10.3.0.1
node2 ansible_host=95.54.0.13 ip=10.3.0.2
node3 ansible_host=95.54.0.14 ip=10.3.0.3
node4 ansible_host=95.54.0.15 ip=10.3.0.4
node5 ansible_host=95.54.0.16 ip=10.3.0.5
node6 ansible_host=95.54.0.17 ip=10.3.0.6

[kube_control_plane]
node1
node2

[etcd]
node1
node2
node3

[kube_node]
node2
node3
node4
node5
node6

[k8s_cluster:children]
kube_node
kube_control_plane
```

## Group vars and overriding variables precedence

The group variables to control main deployment options are located in the directory ``inventory/sample/group_vars``.
Optional variables are located in the `inventory/sample/group_vars/all.yml`.
Mandatory variables that are common for at least one role (or a node group) can be found in the
`inventory/sample/group_vars/k8s_cluster.yml`.
There are also role vars for docker, kubernetes preinstall and control plane roles.
According to the [ansible docs](https://docs.ansible.com/ansible/latest/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable),
those cannot be overridden from the group vars. In order to override, one should use
the `-e` runtime flags (most simple way) or other layers described in the docs.

Kubespray uses only a few layers to override things (or expect them to
be overridden for roles):

| Layer                                  | Comment                                                                      |
|----------------------------------------|------------------------------------------------------------------------------|
| **role defaults**                      | provides best UX to override things for Kubespray deployments                |
| inventory vars                         | Unused                                                                       |
| **inventory group_vars**               | Expects users to use ``all.yml``,``k8s_cluster.yml`` etc. to override things |
| inventory host_vars                    | Unused                                                                       |
| playbook group_vars                    | Unused                                                                       |
| playbook host_vars                     | Unused                                                                       |
| **host facts**                         | Kubespray overrides for internal roles' logic, like state flags              |
| play vars                              | Unused                                                                       |
| play vars_prompt                       | Unused                                                                       |
| play vars_files                        | Unused                                                                       |
| registered vars                        | Unused                                                                       |
| set_facts                              | Kubespray overrides those, for some places                                   |
| **role and include vars**              | Provides bad UX to override things! Use extra vars to enforce                |
| block vars (only for tasks in block)   | Kubespray overrides for internal roles' logic                                |
| task vars (only for the task)          | Unused for roles, but only for helper scripts                                |
| **extra vars** (always win precedence) | override with ``ansible-playbook -e @foo.yml``                               |

## Ansible tags

The following tags are defined in playbooks:

| Tag name                       | Used for                                              |
|--------------------------------|-------------------------------------------------------|
| annotate                       | Create kube-router annotation                         |
| apps                           | K8s apps definitions                                  |
| asserts                        | Check tasks for download role                         |
| aws-ebs-csi-driver             | Configuring csi driver: aws-ebs                       |
| azure-csi-driver               | Configuring csi driver: azure                         |
| bastion                        | Setup ssh config for bastion                          |
| bootstrap-os                   | Anything related to host OS configuration             |
| calico                         | Network plugin Calico                                 |
| calico_rr                      | Configuring Calico route reflector                    |
| cephfs-provisioner             | Configuring CephFS                                    |
| cert-manager                   | Configuring certificate manager for K8s               |
| cilium                         | Network plugin Cilium                                 |
| cinder-csi-driver              | Configuring csi driver: cinder                        |
| client                         | Kubernetes clients role                               |
| cloud-provider                 | Cloud-provider related tasks                          |
| cluster-roles                  | Configuring cluster wide application (psp ...)        |
| cni                            | CNI plugins for Network Plugins                       |
| containerd                     | Configuring containerd engine runtime for hosts       |
| container_engine_accelerator   | Enable nvidia accelerator for runtimes                |
| container-engine               | Configuring container engines                         |
| container-runtimes             | Configuring container runtimes                        |
| coredns                        | Configuring coredns deployment                        |
| crio                           | Configuring crio container engine for hosts           |
| crun                           | Configuring crun runtime                              |
| csi-driver                     | Configuring csi driver                                |
| dashboard                      | Installing and configuring the Kubernetes Dashboard   |
| dns                            | Remove dns entries when resetting                     |
| docker                         | Configuring docker engine runtime for hosts           |
| download                       | Fetching container images to a delegate host          |
| etcd                           | Configuring etcd cluster                              |
| etcd-secrets                   | Configuring etcd certs/keys                           |
| etchosts                       | Configuring /etc/hosts entries for hosts              |
| external-cloud-controller      | Configure cloud controllers                           |
| external-openstack             | Cloud controller : openstack                          |
| external-provisioner           | Configure external provisioners                       |
| external-vsphere               | Cloud controller : vsphere                            |
| facts                          | Gathering facts and misc check results                |
| files                          | Remove files when resetting                           |
| flannel                        | Network plugin flannel                                |
| gce                            | Cloud-provider GCP                                    |
| gcp-pd-csi-driver              | Configuring csi driver: gcp-pd                        |
| gvisor                         | Configuring gvisor runtime                            |
| helm                           | Installing and configuring Helm                       |
| ingress-controller             | Configure ingress controllers                         |
| ingress_alb                    | AWS ALB Ingress Controller                            |
| init                           | Windows kubernetes init nodes                         |
| iptables                       | Flush and clear iptable when resetting                |
| k8s-pre-upgrade                | Upgrading K8s cluster                                 |
| k8s-secrets                    | Configuring K8s certs/keys                            |
| k8s-gen-tokens                 | Configuring K8s tokens                                |
| kata-containers                | Configuring kata-containers runtime                   |
| krew                           | Install and manage krew                               |
| kubeadm                        | Roles linked to kubeadm tasks                         |
| kube-apiserver                 | Configuring static pod kube-apiserver                 |
| kube-controller-manager        | Configuring static pod kube-controller-manager        |
| kube-vip                       | Installing and configuring kube-vip                   |
| kubectl                        | Installing kubectl and bash completion                |
| kubelet                        | Configuring kubelet service                           |
| kube-ovn                       | Network plugin kube-ovn                               |
| kube-router                    | Network plugin kube-router                            |
| kube-proxy                     | Configuring static pod kube-proxy                     |
| localhost                      | Special steps for the localhost (ansible runner)      |
| local-path-provisioner         | Configure External provisioner: local-path            |
| local-volume-provisioner       | Configure External provisioner: local-volume          |
| macvlan                        | Network plugin macvlan                                |
| master                         | Configuring K8s master node role                      |
| metallb                        | Installing and configuring metallb                    |
| metrics_server                 | Configuring metrics_server                            |
| netchecker                     | Installing netchecker K8s app                         |
| network                        | Configuring networking plugins for K8s                |
| mounts                         | Umount kubelet dirs when reseting                     |
| multus                         | Network plugin multus                                 |
| nginx                          | Configuring LB for kube-apiserver instances           |
| node                           | Configuring K8s minion (compute) node role            |
| nodelocaldns                   | Configuring nodelocaldns daemonset                    |
| node-label                     | Tasks linked to labeling of nodes                     |
| node-webhook                   | Tasks linked to webhook (grating access to resources) |
| nvidia_gpu                     | Enable nvidia accelerator for runtimes                |
| oci                            | Cloud provider: oci                                   |
| persistent_volumes             | Configure csi volumes                                 |
| persistent_volumes_aws_ebs_csi | Configuring csi driver: aws-ebs                       |
| persistent_volumes_cinder_csi  | Configuring csi driver: cinder                        |
| persistent_volumes_gcp_pd_csi  | Configuring csi driver: gcp-pd                        |
| persistent_volumes_openstack   | Configuring csi driver: openstack                     |
| policy-controller              | Configuring Calico policy controller                  |
| post-remove                    | Tasks running post-remove operation                   |
| post-upgrade                   | Tasks running post-upgrade operation                  |
| pre-remove                     | Tasks running pre-remove operation                    |
| pre-upgrade                    | Tasks running pre-upgrade operation                   |
| preinstall                     | Preliminary configuration steps                       |
| registry                       | Configuring local docker registry                     |
| reset                          | Tasks running doing the node reset                    |
| resolvconf                     | Configuring /etc/resolv.conf for hosts/apps           |
| rbd-provisioner                | Configure External provisioner: rdb                   |
| services                       | Remove services (etcd, kubelet etc...) when resetting |
| snapshot                       | Enabling csi snapshot                                 |
| snapshot-controller            | Configuring csi snapshot controller                   |
| upgrade                        | Upgrading, f.e. container images/binaries             |
| upload                         | Distributing images/binaries across hosts             |
| vsphere-csi-driver             | Configuring csi driver: vsphere                       |
| weave                          | Network plugin Weave                                  |
| win_nodes                      | Running windows specific tasks                        |
| youki                          | Configuring youki runtime                             |

Note: Use the ``bash scripts/gen_tags.sh`` command to generate a list of all
tags found in the codebase. New tags will be listed with the empty "Used for"
field.

## Example commands

Example command to filter and apply only DNS configuration tasks and skip
everything else related to host OS configuration and downloading images of containers:

```ShellSession
ansible-playbook -i inventory/sample/hosts.ini cluster.yml --tags preinstall,facts --skip-tags=download,bootstrap-os
```

And this play only removes the K8s cluster DNS resolver IP from hosts' /etc/resolv.conf files:

```ShellSession
ansible-playbook -i inventory/sample/hosts.ini -e dns_mode='none' cluster.yml --tags resolvconf
```

And this prepares all container images locally (at the ansible runner node) without installing
or upgrading related stuff or trying to upload container to K8s cluster nodes:

```ShellSession
ansible-playbook -i inventory/sample/hosts.ini cluster.yml \
    -e download_run_once=true -e download_localhost=true \
    --tags download --skip-tags upload,upgrade
```

Note: use `--tags` and `--skip-tags` wise and only if you're 100% sure what you're doing.

## Bastion host

If you prefer to not make your nodes publicly accessible (nodes with private IPs only),
you can use a so-called _bastion_ host to connect to your nodes. To specify and use a bastion,
simply add a line to your inventory, where you have to replace x.x.x.x with the public IP of the
bastion host.

```ShellSession
[bastion]
bastion ansible_host=x.x.x.x
```

For more information about Ansible and bastion hosts, read
[Running Ansible Through an SSH Bastion Host](https://blog.scottlowe.org/2015/12/24/running-ansible-through-ssh-bastion-host/)

## Mitogen

Mitogen support is deprecated, please see [mitogen related docs](/docs/mitogen.md) for usage and reasons for deprecation.

## Beyond ansible 2.9

Ansible project has decided, in order to ease their maintenance burden, to split between
two projects which are now joined under the Ansible umbrella.

Ansible-base (2.10.x branch) will contain just the ansible language implementation while
ansible modules that were previously bundled into a single repository will be part of the
ansible 3.x package. Please see [this blog post](https://blog.while-true-do.io/ansible-release-3-0-0/)
that explains in detail the need and the evolution plan.

**Note:** this change means that ansible virtual envs cannot be upgraded with `pip install -U`.
You first need to uninstall your old ansible (pre 2.10) version and install the new one.

```ShellSession
pip uninstall ansible ansible-base ansible-core
cd kubespray/
pip install -U .
```
