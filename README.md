kubernetes-ansible
========

Install and configure a kubernetes cluster including network overlay and optionnal addons.
Based on [CiscoCloud](https://github.com/CiscoCloud/kubernetes-ansible) work.

### Requirements
Tested on debian Jessie and Ubuntu.
The target servers must have access to the Internet in order to pull docker imaqes

Ansible v1.9.x

### Components
* [kubernetes]('https://github.com/kubernetes/kubernetes/releases') v1.0.6
* [etcd]('https://github.com/coreos/etcd/releases') v2.2.0
* [calicoctl]('https://github.com/projectcalico/calico-docker/releases') v0.5.1
* [flanneld]('https://github.com/coreos/flannel/releases') v0.5.3
* [docker-gc]('https://github.com/spotify/docker-gc')


Ansible
-------------------------
### Download binaries
A role allows to download required binaries which will be stored in a directory defined by the variable
'local_release_dir' (by default /tmp).
Please ensure that you have enough disk space there (about 1G).

Note: Whenever you'll need to change the version of a software, you'll have to erase the content of this directory.


### Variables

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
    - { role: overlay_network, tags: ['calico', 'flannel', 'network'] }
    - { role: dnsmasq, tags: dnsmasq }

- hosts: kube-master
  roles:
    - { role: kubernetes/master, tags: master }
    - { role: addons, tags: addons }

- hosts: kube-node
  roles:
    - { role: kubernetes/node, tags: node }
```

### Run
It is possible to define variables for different environments.
For instance, in order to deploy the cluster on 'dev' environment run the following command.
```
ansible-playbook -i environments/dev/inventory cluster.yml
```

Kubernetes
-------------------------
### Check cluster status

### Network Overlay
You can choose between 2 network overlays. Only one must be chosen.
flannel: gre/vxlan (layer 2) networking
calico: bgp (layer 3) networking.

### Expose a service
There are several loadbalancing solution.
The main ones i found suitable for kubernetes are [Vulcand]('http://vulcand.io/') and [Haproxy]('http://www.haproxy.org/')

My cluster is working with haproxy and kubernetes services are configured with the loadbalancing type 'nodePort'.
eg: each node opens the same tcp port and forwards the traffic to the target pod wherever it is located.

Then Haproxy can be configured to request kubernetes's api in order to loadbalance on the proper tcp port on the nodes.

Please refer to the proper kubernetes documentation on [Services]('https://github.com/kubernetes/kubernetes/blob/release-1.0/docs/user-guide/services.md')

Known issues
-------------
### Node reboot and Calico

### Monitoring addon

### Etcd failover

Author Information
------------------

Smana - Smaine Kahlouch (smaine.kahlouch@gmail.com)
