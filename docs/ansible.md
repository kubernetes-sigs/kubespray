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
