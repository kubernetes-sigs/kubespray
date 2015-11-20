kubernetes-ansible
========

Install and configure a kubernetes cluster including network plugin and optionnal addons.
Based on [CiscoCloud](https://github.com/CiscoCloud/kubernetes-ansible) work.

### Requirements
Tested on **Debian Jessie** and **Ubuntu** (14.10, 15.04, 15.10).
The target servers must have access to the Internet in order to pull docker imaqes.
The firewalls are not managed, you'll need to implement your own rules the way you used to.

Ansible v1.9.x

### Components
* [kubernetes](https://github.com/kubernetes/kubernetes/releases) v1.0.6
* [etcd](https://github.com/coreos/etcd/releases) v2.2.0
* [calicoctl](https://github.com/projectcalico/calico-docker/releases) v0.5.1
* [flanneld](https://github.com/coreos/flannel/releases) v0.5.3
* [docker](https://www.docker.com/) v1.8.3


Ansible
-------------------------
### Download binaries
A role allows to download required binaries which will be stored in a directory defined by the variable
**'local_release_dir'** (by default /tmp).
Please ensure that you have enough disk space there (about **1G**).

**Note**: Whenever you'll need to change the version of a software, you'll have to erase the content of this directory.


### Variables
The main variables to change are located in the directory ```environments/[env_name]/group_vars/k8s-cluster.yml```.

### Inventory
Below is an example of an inventory.
Note : The bgp vars local_as and peers are not mandatory if the var "peer_with_router" is set to false
By default this variable is set to false and therefore all the nodes are configure in "node-mesh" mode.
In node-mesh mode the nodes peers with all the nodes in order to exchange routes.

```
[downloader]
10.99.0.26

[kube-master]
# NB : the br_addr must be in the {{ calico_pool }} subnet
# it will assign a /24 subnet per node
10.99.0.26 br_addr=10.99.64.1

[etcd]
10.99.0.26

[kube-node]
10.99.0.4
10.99.0.5
10.99.0.6
10.99.0.36
10.99.0.37

[itx2]
10.99.0.26 br_addr=10.99.16.1
10.99.0.4 br_addr=10.99.65.1 local_as=xxxxxxxx
10.99.0.5 br_addr=10.99.66.1 local_as=xxxxxxxx
10.99.0.6 br_addr=10.99.69.1 local_as=xxxxxxxx

[rmv]
10.99.0.36 br_addr=10.99.67.1 local_as=xxxxxxxx
10.99.0.37 br_addr=10.99.68.1 local_as=xxxxxxxx

[k8s-cluster:children]
kube-node
kube-master

[itx2:vars]
peers=[{"router_id": "10.99.0.2", "as": "65xxx"}, {"router_id": "10.99.0.3", "as": "65xxx"}]

[rmv:vars]
peers=[{"router_id": "10.99.0.34", "as": "65xxx"}, {"router_id": "10.99.0.35", "as": "65xxx"}]
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
    - { role: etcd, tags: etcd }
    - { role: docker, tags: docker }
    - { role: network_plugin, tags: ['calico', 'flannel', 'network'] }
    - { role: dnsmasq, tags: dnsmasq }

- hosts: kube-master
  roles:
    - { role: kubernetes/master, tags: master }

- hosts: kube-node
  roles:
    - { role: kubernetes/node, tags: node }

- hosts: kube-master
  roles:
    - { role: apps/k8s-kubedns, tags: ['kubedns', 'apps']  }
    - { role: apps/k8s-fabric8, tags: ['fabric8', 'apps']  }
```

### Run
It is possible to define variables for different environments.
For instance, in order to deploy the cluster on 'dev' environment run the following command.
```
ansible-playbook -i environments/dev/inventory cluster.yml -u root
```

Kubernetes
-------------------------

### Network Overlay
You can choose between 2 network plugins. Only one must be chosen.

* **flannel**: gre/vxlan (layer 2) networking. ([official docs]('https://github.com/coreos/flannel'))

* **calico**: bgp (layer 3) networking. ([official docs]('http://docs.projectcalico.org/en/0.13/'))

The choice is defined with the variable '**kube_network_plugin**'

### Expose a service
There are several loadbalancing solutions.
The ones i found suitable for kubernetes are [Vulcand]('http://vulcand.io/') and [Haproxy]('http://www.haproxy.org/')

My cluster is working with haproxy and kubernetes services are configured with the loadbalancing type '**nodePort**'.
eg: each node opens the same tcp port and forwards the traffic to the target pod wherever it is located.

Then Haproxy can be configured to request kubernetes's api in order to loadbalance on the proper tcp port on the nodes.

Please refer to the proper kubernetes documentation on [Services]('https://github.com/kubernetes/kubernetes/blob/release-1.0/docs/user-guide/services.md')

### Check cluster status

#### Kubernetes components
Master processes : kube-apiserver, kube-scheduler, kube-controller, kube-proxy
Nodes processes : kubelet, kube-proxy, [calico-node|flanneld]

* Check the status of the processes
```
systemctl status [process_name]
```

* Check the logs
```
journalctl -ae -u [process_name]
```

* Check the NAT rules
```
iptables -nLv -t nat
```


### Available apps, installation procedure

There are two ways of installing new apps

#### Ansible galaxy

Additionnal apps can be installed with ```ansible-galaxy```.

you'll need to edit the file '*requirements.yml*' in order to chose needed apps.
The list of available apps are available [there](https://github.com/ansibl8s)

For instance if you will probably want to install a [dns server](https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/dns) as it is **strongly recommanded**.
In order to use this role you'll need the following entries in the file '*requirements.yml*' 
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

For instance if you will probably want to install a [dns server](https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/dns) as it is **strongly recommanded**.
Please refer to the [k8s-kubdns readme](https://github.com/ansibl8s/k8s-kubedns) for additionnal info.

In order to use this role you'll need to follow these steps
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
ansible-playbook -i environments/dev/inventory apps.yml -u root
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

Congrats ! now you can walk through [kubernetes basics](http://kubernetes.io/v1.0/basicstutorials.html)

Known issues
-------------
### Node reboot and Calico
There is a major issue with calico-kubernetes version 0.5.1 and kubernetes prior to 1.1 :
After host reboot, the pods networking are not configured again, they are started without any network configuration.
This issue will be fixed when kubernetes 1.1 will be released as described in this [issue](https://github.com/projectcalico/calico-kubernetes/issues/34)

### Monitoring addon
Until now i didn't managed to get the monitoring addon working.

### Apiserver listen on secure port only
Currently the api-server listens on both secure and insecure ports.
The insecure port is mainly used for calico.
Will be fixed soon.
