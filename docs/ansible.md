Ansible variables
===============


Inventory
-------------
The inventory is composed of 3 groups:

* **kube-node** : list of kubernetes nodes where the pods will run.
* **kube-master** : list of servers where kubernetes master components (apiserver, scheduler, controller) will run.
  Note: if you want the server to act both as master and node the server must be defined on both groups _kube-master_ and _kube-node_
* **etcd**: list of server to compose the etcd server. you should have at least 3 servers for failover purposes.

Below is a complete inventory example:

```
## Configure 'ip' variable to bind kubernetes services on a
## different ip than the default iface
node1 ansible_ssh_host=95.54.0.12  # ip=10.3.0.1
node2 ansible_ssh_host=95.54.0.13  # ip=10.3.0.2
node3 ansible_ssh_host=95.54.0.14  # ip=10.3.0.3
node4 ansible_ssh_host=95.54.0.15  # ip=10.3.0.4
node5 ansible_ssh_host=95.54.0.16  # ip=10.3.0.5
node6 ansible_ssh_host=95.54.0.17  # ip=10.3.0.6

[kube-master]
node1
node2

[etcd]
node1
node2
node3

[kube-node]
node2
node3
node4
node5
node6

[k8s-cluster:children]
kube-node
kube-master
etcd
```

Group vars
--------------
The main variables to change are located in the directory ```inventory/group_vars/all.yml```.

Ansible tags
------------

The following tags are defined in playbooks:

|                 Tag name | Used for
|--------------------------|---------
|                     apps | K8s apps definitions
|                    azure | Cloud-provider Azure
|             bootstrap-os | Anything related to host OS configuration
|                   calico | Network plugin Calico
|                    canal | Network plugin Canal
|           cloud-provider | Cloud-provider related tasks
|                  dnsmasq | Configuring DNS stack for hosts and K8s apps
|                   docker | Configuring docker for hosts
|                 download | Fetching container images
|                     etcd | Configuring etcd cluster
|         etcd-pre-upgrade | Upgrading etcd cluster
|             etcd-secrets | Configuring etcd certs/keys
|                 etchosts | Configuring /etc/hosts entries for hosts
|                    facts | Gathering facts and misc check results
|                  flannel | Network plugin flannel
|                      gce | Cloud-provider GCP
|                hyperkube | Manipulations with K8s hyperkube image
|          k8s-pre-upgrade | Upgrading K8s cluster
|              k8s-secrets | Configuring K8s certs/keys
|                      kpm | Installing K8s apps definitions with KPM
|           kube-apiserver | Configuring self-hosted kube-apiserver
|  kube-controller-manager | Configuring self-hosted kube-controller-manager
|                  kubectl | Installing kubectl and bash completion
|                  kubelet | Configuring kubelet service
|               kube-proxy | Configuring self-hosted kube-proxy
|           kube-scheduler | Configuring self-hosted kube-scheduler
|                   master | Configuring K8s master node role
|               netchecker | Installing netchecker K8s app
|                  network | Configuring networking plugins for K8s
|                    nginx | Configuring LB for kube-apiserver instances
|                     node | Configuring K8s minion (compute) node role
|                openstack | Cloud-provider OpenStack
|               preinstall | Preliminary configuration steps
|               resolvconf | Configuring /etc/resolv.conf for hosts/apps
|                  upgrade | Upgrading, f.e. container images/binaries
|                    weave | Network plugin Weave

Note: Use the ``bash scripts/gen_tags.sh`` command to generate a list of all
tags found in the codebase. New tags will be listed with the empty "Used for"
field.

Example command to filter and apply only DNS configuration tasks and skip
everything else related to host OS configuration and downloading images of containers:

```
ansible-playbook -i inventory/inventory.ini cluster.yml  --tags preinstall,dnsmasq,facts --skip-tags=download,bootstrap-os
```
And this play only removes the K8s cluster DNS resolver IP from hosts' /etc/resolv.conf files:
```
ansible-playbook -i inventory/inventory.ini -e dns_server='' cluster.yml --tags resolvconf
```

Note: use `--tags` and `--skip-tags` wise and only if you're 100% sure what you're doing.
