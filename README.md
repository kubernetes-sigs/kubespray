[![Build Status](https://travis-ci.org/ansibl8s/setup-kubernetes.svg)](https://travis-ci.org/ansibl8s/setup-kubernetes)
kubernetes-ansible
========

Install and configure a Multi-Master/HA kubernetes cluster including network plugin.

Linux distributions tested:
* **Debian** Wheezy, Jessie
* **Ubuntu** 14.10, 15.04, 15.10
* **Fedora** 23
* **CentOS** (Currently with flannel only)

### Requirements
* The target servers must have **access to the Internet** in order to pull docker imaqes.
* The firewalls are not managed, you'll need to implement your own rules the way you used to.
in order to avoid any issue during deployment you should **disable your firewall**
* **Copy your ssh keys** to all the servers part of your inventory.
* **Ansible v1.9.x and python-netaddr**

### Components
* [kubernetes](https://github.com/kubernetes/kubernetes/releases) v1.1.3
* [etcd](https://github.com/coreos/etcd/releases) v2.2.2
* [calicoctl](https://github.com/projectcalico/calico-docker/releases) v0.13.0
* [flanneld](https://github.com/coreos/flannel/releases) v0.5.5
* [docker](https://www.docker.com/) v1.9.1

Quickstart
-------------------------
The following steps will quickly setup a kubernetes cluster with default configuration.
These defaults are good for tests purposes.

Edit the inventory according to the number of servers
```
[downloader]
localhost ansible_connection=local ansible_python_interpreter=python2

[kube-master]
10.115.99.31

[etcd]
10.115.99.31
10.115.99.32
10.115.99.33

[kube-node]
10.115.99.32
10.115.99.33

[k8s-cluster:children]
kube-node
kube-master
```

Run the playbook
```
ansible-playbook -i inventory/inventory.cfg cluster.yml -u root
```

You can jump directly to "*Available apps, installation procedure*"


Ansible
-------------------------
### Variables
The main variables to change are located in the directory ```inventory/group_vars/all.yml```.

### Inventory
Below is an example of an inventory.
Note : The bgp vars local_as and peers are not mandatory if the var **'peer_with_router'** is set to false
By default this variable is set to false and therefore all the nodes are configure in **'node-mesh'** mode.
In node-mesh mode the nodes peers with all the nodes in order to exchange routes.

```

[downloader]
localhost ansible_connection=local ansible_python_interpreter=python2

[kube-master]
node1 ansible_ssh_host=10.99.0.26
node2 ansible_ssh_host=10.99.0.27

[etcd]
node1 ansible_ssh_host=10.99.0.26
node2 ansible_ssh_host=10.99.0.27
node3 ansible_ssh_host=10.99.0.4

[kube-node]
node2 ansible_ssh_host=10.99.0.27
node3 ansible_ssh_host=10.99.0.4
node4 ansible_ssh_host=10.99.0.5
node5 ansible_ssh_host=10.99.0.36
node6 ansible_ssh_host=10.99.0.37

[paris]
node1 ansible_ssh_host=10.99.0.26
node3 ansible_ssh_host=10.99.0.4 local_as=xxxxxxxx
node4 ansible_ssh_host=10.99.0.5 local_as=xxxxxxxx

[new-york]
node2 ansible_ssh_host=10.99.0.27
node5 ansible_ssh_host=10.99.0.36 local_as=xxxxxxxx
node6 ansible_ssh_host=10.99.0.37 local_as=xxxxxxxx

[k8s-cluster:children]
kube-node
kube-master
```

### Playbook
```
---
- hosts: downloader
  sudo: no
  roles:
    - { role: download, tags: download }

- hosts: k8s-cluster
  roles:
    - { role: kubernetes/preinstall, tags: preinstall }
    - { role: docker, tags: docker }
    - { role: kubernetes/node, tags: node }
    - { role: etcd, tags: etcd }
    - { role: dnsmasq, tags: dnsmasq }
    - { role: network_plugin, tags: ['calico', 'flannel', 'network'] }

- hosts: kube-master
  roles:
    - { role: kubernetes/master, tags: master }

```

### Run
It is possible to define variables for different environments.
For instance, in order to deploy the cluster on 'dev' environment run the following command.
```
ansible-playbook -i inventory/dev/inventory.cfg cluster.yml -u root
```

Kubernetes
-------------------------
### Multi master notes
* You can choose where to install the master components. If you want your master node to act both as master (api,scheduler,controller) and node (e.g. accept workloads, create pods ...), 
the server address has to be present on both groups 'kube-master' and 'kube-node'.

* Almost all kubernetes components are running into pods except *kubelet*. These pods are managed by kubelet which ensure they're always running

* For safety reasons, you should have at least two master nodes and 3 etcd servers

* Kube-proxy doesn't support multiple apiservers on startup ([Issue 18174](https://github.com/kubernetes/kubernetes/issues/18174)). An external loadbalancer needs to be configured.
In order to do so, some variables have to be used '**loadbalancer_apiserver**' and '**apiserver_loadbalancer_domain_name**' 
 

### Network Overlay
You can choose between 2 network plugins. Only one must be chosen.

* **flannel**: gre/vxlan (layer 2) networking. ([official docs](https://github.com/coreos/flannel))

* **calico**: bgp (layer 3) networking. ([official docs](http://docs.projectcalico.org/en/0.13/))

The choice is defined with the variable '**kube_network_plugin**'

### Expose a service
There are several loadbalancing solutions.
The one i found suitable for kubernetes are [Vulcand](http://vulcand.io/) and [Haproxy](http://www.haproxy.org/)

My cluster is working with haproxy and kubernetes services are configured with the loadbalancing type '**nodePort**'.
eg: each node opens the same tcp port and forwards the traffic to the target pod wherever it is located.

Then Haproxy can be configured to request kubernetes's api in order to loadbalance on the proper tcp port on the nodes.

Please refer to the proper kubernetes documentation on [Services](https://github.com/kubernetes/kubernetes/blob/release-1.0/docs/user-guide/services.md)

### Check cluster status

#### Kubernetes components

* Check the status of the processes
```
systemctl status kubelet
```

* Check the logs
```
journalctl -ae -u kubelet
```

* Check the NAT rules
```
iptables -nLv -t nat
```

For the master nodes you'll have to see the docker logs for the apiserver
```
docker logs [apiserver docker id]
```


### Available apps, installation procedure

There are two ways of installing new apps

#### Ansible galaxy

Additionnal apps can be installed with ```ansible-galaxy```.

ou'll need to edit the file '*requirements.yml*' in order to chose needed apps.
The list of available apps are available [there](https://github.com/ansibl8s)

For instance it is **strongly recommanded** to install a dns server which resolves kubernetes service names.
In order to use this role you'll need the following entries in the file '*requirements.yml*' 
Please refer to the [k8s-kubedns readme](https://github.com/ansibl8s/k8s-kubedns) for additionnal info.
```
- src: https://github.com/ansibl8s/k8s-common.git
  path: roles/apps
  # version: v1.0

- src: https://github.com/ansibl8s/k8s-kubedns.git
  path: roles/apps
  # version: v1.0
```
**Note**: the role common is required by all the apps and provides the tasks and libraries needed.

And empty the apps directory
```
rm -rf roles/apps/*
```

Then download the roles with ansible-galaxy
```
ansible-galaxy install -r requirements.yml
```

#### Git submodules
Alternatively the roles can be installed as git submodules.
That way is easier if you want to do some changes and commit them.

You can list available submodules with the following command:
```
grep path .gitmodules | sed 's/.*= //'
```

In order to install the dns addon you'll need to follow these steps
```
git submodule init roles/apps/k8s-common roles/apps/k8s-kubedns
git submodule update
```

Finally update the playbook ```apps.yml``` with the chosen roles, and run it
```
...
- hosts: kube-master
  roles:
    - { role: apps/k8s-kubedns, tags: ['kubedns', 'apps']  }
...
```

```
ansible-playbook -i inventory/inventory.cfg apps.yml -u root
```


#### Calico networking
Check if the calico-node container is running
```
docker ps | grep calico
```

The **calicoctl** command allows to check the status of the network workloads.
* Check the status of Calico nodes
```
calicoctl status
```

* Show the configured network subnet for containers
```
calicoctl pool show
```

* Show the workloads (ip addresses of containers and their located)
```
calicoctl endpoint show --detail
```

#### Flannel networking

* Flannel configuration file should have been created there
```
cat /run/flannel/subnet.env
FLANNEL_NETWORK=10.233.0.0/18
FLANNEL_SUBNET=10.233.16.1/24
FLANNEL_MTU=1450
FLANNEL_IPMASQ=false
```

* Check if the network interface has been created
```
ip a show dev flannel.1
4: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN group default 
    link/ether e2:f3:a7:0f:bf:cb brd ff:ff:ff:ff:ff:ff
    inet 10.233.16.0/18 scope global flannel.1
       valid_lft forever preferred_lft forever
    inet6 fe80::e0f3:a7ff:fe0f:bfcb/64 scope link 
       valid_lft forever preferred_lft forever
```

* Docker must be configured with a bridge ip in the flannel subnet.
```
ps aux | grep docker
root     20196  1.7  2.7 1260616 56840 ?       Ssl  10:18   0:07 /usr/bin/docker daemon --bip=10.233.16.1/24 --mtu=1450
```

* Try to run a container and check its ip address
```
kubectl run test --image=busybox --command -- tail -f /dev/null
replicationcontroller "test" created

kubectl describe po test-34ozs | grep ^IP
IP:				10.233.16.2
```

```
kubectl exec test-34ozs -- ip a show dev eth0
8: eth0@if9: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1450 qdisc noqueue 
    link/ether 02:42:0a:e9:2b:03 brd ff:ff:ff:ff:ff:ff
    inet 10.233.16.2/24 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:aff:fee9:2b03/64 scope link tentative flags 08 
       valid_lft forever preferred_lft forever
```


Congrats ! now you can walk through [kubernetes basics](http://kubernetes.io/v1.1/basicstutorials.html)
