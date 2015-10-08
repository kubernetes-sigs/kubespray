kubernetes-ansible
========

Install and configure a kubernetes cluster including network overlay and optionnal addons.
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
* [docker](https://www.docker.com/) v1.8.2


Ansible
-------------------------
### Download binaries
A role allows to download required binaries which will be stored in a directory defined by the variable
**'local_release_dir'** (by default /tmp).
Please ensure that you have enough disk space there (about **1G**).

**Note**: Whenever you'll need to change the version of a software, you'll have to erase the content of this directory.


### Variables
The main variables to change are located in the directory ```environments/[env_name]/group_vars/k8s-cluster.yml```.

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
ansible-playbook -i environments/dev/inventory cluster.yml -u root
```

Kubernetes
-------------------------

### Network Overlay
You can choose between 2 network overlays. Only one must be chosen.

* **flannel**: gre/vxlan (layer 2) networking. ([official docs]('https://github.com/coreos/flannel'))

* **calico**: bgp (layer 3) networking. ([official docs]('http://docs.projectcalico.org/en/0.13/'))

The choice is defined with the variable '**overlay_network_plugin**'

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


#### Available addons
By default 3 addons are enabled
* A dns server in order to resolve kubernetes services names
* [Kube-ui](https://github.com/kubernetes/kube-ui) which is a simple dashboard which shows kubernete's components, url : ``` http://[master_ip]:8080/ui```
* [Fabric8](http://fabric8.io/), console management for kubernetes : ```http://[master_ip]:8080/api/v1/proxy/namespaces/default/services/fabric8``` 

Other addons : logging, monitoring


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

#### Test the dns server
* Create a file 'busybox.yaml' with the following content
```
apiVersion: v1
kind: Pod
metadata:
  name: busybox
  namespace: default
spec:
  containers:
  - image: busybox
    command:
      - sleep
      - "3600"
    imagePullPolicy: IfNotPresent
    name: busybox
  restartPolicy: Always
```

* Create the pod
```
kubectl create -f busybox.yaml
```

* When the pod is ready, execute the following command
```
kubectl exec busybox -- nslookup kubernetes.default
```
You should get an answer from the configured dns server

Congrats ! now you can walk through [kubernetes basics](http://kubernetes.io/v1.0/basicstutorials.html)

Known issues
-------------
### Node reboot and Calico
There is a major issue with calico-kubernetes version 0.5.1 and kubernetes prior to 1.1 :
After host reboot, the pods networking are not configured again, they are started without any network configuration.
This issue will be fixed when kubernetes 1.1 will be released as described in this [issue](https://github.com/projectcalico/calico-kubernetes/issues/34)

### Monitoring addon
Until now i didn't managed to get the monitoring addon working.

### Listen on secure port only
Currently the api-server listens on both secure and insecure ports.
The insecure port is mainly used for calico.
Will be fixed soon.

Author Information
------------------

Smana - Smaine Kahlouch (smainklh@gmail.com)
