# Inventory

The inventory is composed of 3 groups:

* **kube_node** : list of kubernetes nodes where the pods will run.
* **kube_control_plane** : list of servers where kubernetes control plane components (apiserver, scheduler, controller) will run.
* **etcd**: list of servers to compose the etcd server. You should have at least 3 servers for failover purpose.

When _kube_node_ contains _etcd_, you define your etcd cluster to be as well schedulable for Kubernetes workloads.
If you want it a standalone, make sure those groups do not intersect.
If you want the server to act both as control-plane and node, the server must be defined
on both groups _kube_control_plane_ and _kube_node_. If you want a standalone and
unschedulable control plane, the server must be defined only in the _kube_control_plane_ and
not _kube_node_.

There are also two special groups:

* **calico_rr** : explained for [advanced Calico networking cases](/docs/CNI/calico.md)
* **bastion** : configure a bastion host if your nodes are not directly reachable

Lastly, the **k8s_cluster** is dynamically defined as the union of **kube_node**, **kube_control_plane** and **calico_rr**.
This is used internally and for the purpose of defining whole cluster variables (`<inventory>/group_vars/k8s_cluster/*.yml`)

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
```

## Inventory customization

See [Customize Ansible vars](/docs/ansible/ansible.md#customize-ansible-vars)
and [Ansible documentation on group_vars](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html#assigning-a-variable-to-many-machines-group-variables)

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
