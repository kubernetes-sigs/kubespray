[![Build Status](https://travis-ci.org/kubespray/setup-kubernetes.svg)](https://travis-ci.org/kubespray/setup-kubernetes)
kubernetes-ansible
========

This project allows to
- Install and configure a **Multi-Master/HA kubernetes** cluster.
- Choose the **network plugin** to be used within the cluster
- A **set of roles** in order to install applications over the k8s cluster
- A **flexible method** which helps to create new roles for apps.

Linux distributions tested:
* **Debian** Wheezy, Jessie
* **Ubuntu** 14.10, 15.04, 15.10
* **Fedora** 23
* **CentOS/RHEL** 7
* **CoreOS**

### Requirements
* The target servers must have **access to the Internet** in order to pull docker imaqes.
* The **firewalls are not managed**, you'll need to implement your own rules the way you used to.
in order to avoid any issue during deployment you should disable your firewall
* **Copy your ssh keys** to all the servers part of your inventory.
* **Ansible v2.x and python-netaddr**
* Base knowledge on Ansible. Please refer to [Ansible documentation](http://www.ansible.com/how-ansible-works)

### Components
* [kubernetes](https://github.com/kubernetes/kubernetes/releases) v1.1.8
* [etcd](https://github.com/coreos/etcd/releases) v2.2.5
* [calicoctl](https://github.com/projectcalico/calico-docker/releases) v0.17.0
* [flanneld](https://github.com/coreos/flannel/releases) v0.5.5
* [weave](http://weave.works/) v1.4.4
* [docker](https://www.docker.com/) v1.9

Quickstart
-------------------------
The following steps will quickly setup a kubernetes cluster with default configuration.
These defaults are good for tests purposes.

Edit the inventory according to the number of servers
```
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
```

Run the playbook
```
ansible-playbook -i inventory/inventory.cfg cluster.yml -u root
```

You can jump directly to "*Available apps, installation procedure*"


Ansible
-------------------------
### Coreos bootstrap
Before running the cluster playbook you must satisfy the following requirements:
* On each CoreOS nodes a writable directory **/opt/bin** (~400M disk space)

* Uncomment the variable **ansible_python_interpreter** in the file `inventory/group_vars/all.yml`

* run the Python bootstrap playbook
```
ansible-playbook -u smana -e ansible_ssh_user=smana  -b --become-user=root -i inventory/inventory.cfg coreos-bootstrap.yml
```
Then you can proceed to cluster deployment

### Variables
The main variables to change are located in the directory ```inventory/group_vars/all.yml```.

### Inventory
Below is an example of an inventory.

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
```

### Playbook
```
---
- hosts: k8s-cluster
  roles:
    - { role: adduser, tags: adduser }
    - { role: download, tags: download }
    - { role: kubernetes/preinstall, tags: preinstall }
    - { role: etcd, tags: etcd }
    - { role: docker, tags: docker }
    - { role: kubernetes/node, tags: node }
    - { role: network_plugin, tags: network }
    - { role: dnsmasq, tags: dnsmasq }

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

* For safety reasons, you should have at least two master nodes and 3 etcd servers

* Kube-proxy doesn't support multiple apiservers on startup ([Issue 18174](https://github.com/kubernetes/kubernetes/issues/18174)). An external loadbalancer needs to be configured.
In order to do so, some variables have to be used '**loadbalancer_apiserver**' and '**apiserver_loadbalancer_domain_name**'


### Network Plugin
You can choose between 3 network plugins. Only one must be chosen.

* **flannel**: gre/vxlan (layer 2) networking. ([official docs](https://github.com/coreos/flannel))

* **calico**: bgp (layer 3) networking. ([official docs](http://docs.projectcalico.org/en/0.13/))

* **weave**: Weave is a lightweight container overlay network that doesn't require an external K/V database cluster. ([official docs](http://weave.works/docs/))

The choice is defined with the variable **kube_network_plugin**


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

you'll need to edit the file '*requirements.yml*' in order to chose needed apps.
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

#### Git submodules
Alternatively the roles can be installed as git submodules.
That way is easier if you want to do some changes and commit them.


### Networking

#### Calico
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

##### Optionnal : BGP Peering with border routers

In some cases you may want to route the pods subnet and so NAT is not needed on the nodes.
For instance if you have a cluster spread on different locations and you want your pods to talk each other no matter where they are located.
The following variables need to be set:
**peer_with_router**  enable the peering with border router of the datacenter (default value: false).
you'll need to edit the inventory and add a and a hostvar **local_as** by node. 
```
node1 ansible_ssh_host=95.54.0.12 local_as=xxxxxx
```


#### Flannel

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
