Calico
===========

Check if the calico-node container is running

```
docker ps | grep calico
```

The **calicoctl** command allows to check the status of the network workloads.
* Check the status of Calico nodes

```
calicoctl node status
```

or for versions prior *v1.0.0*:

```
calicoctl status
```

* Show the configured network subnet for containers

```
calicoctl get ippool -o wide
```

or for versions prior *v1.0.0*:

```
calicoctl pool show
```

* Show the workloads (ip addresses of containers and their located)

```
calicoctl get workloadEndpoint -o wide
```

and

```
calicoctl get hostEndpoint -o wide
```

or for versions prior *v1.0.0*:

```
calicoctl endpoint show --detail
```

##### Optional : Define network backend

In some cases you may want to define Calico network backend. Allowed values are 'bird', 'gobgp' or 'none'. Bird is a default value.

To re-define you need to edit the inventory and add a group variable `calico_network_backend`

```
calico_network_backend: none
```

##### Optional : BGP Peering with border routers

In some cases you may want to route the pods subnet and so NAT is not needed on the nodes.
For instance if you have a cluster spread on different locations and you want your pods to talk each other no matter where they are located.
The following variables need to be set:
`peer_with_router` to enable the peering with the datacenter's border router (default value: false).
you'll need to edit the inventory and add a and a hostvar `local_as` by node.

```
node1 ansible_ssh_host=95.54.0.12 local_as=xxxxxx
```

##### Optional : Define global AS number

Optional parameter `global_as_num` defines Calico global AS number (`/calico/bgp/v1/global/as_num` etcd key).
It defaults to "64512".

##### Optional : BGP Peering with route reflectors

At large scale you may want to disable full node-to-node mesh in order to
optimize your BGP topology and improve `calico-node` containers' start times.

To do so you can deploy BGP route reflectors and peer `calico-node` with them as
recommended here:

* https://hub.docker.com/r/calico/routereflector/
* http://docs.projectcalico.org/v2.0/reference/private-cloud/l3-interconnect-fabric

You need to edit your inventory and add:

* `calico-rr` group with nodes in it. At the moment it's incompatible with
  `kube-node` due to BGP port conflict with `calico-node` container. So you
  should not have nodes in both `calico-rr` and `kube-node` groups.
* `cluster_id` by route reflector node/group (see details
[here](https://hub.docker.com/r/calico/routereflector/))

Here's an example of Kargo inventory with route reflectors:

```
[all]
rr0 ansible_ssh_host=10.210.1.10 ip=10.210.1.10
rr1 ansible_ssh_host=10.210.1.11 ip=10.210.1.11
node2 ansible_ssh_host=10.210.1.12 ip=10.210.1.12
node3 ansible_ssh_host=10.210.1.13 ip=10.210.1.13
node4 ansible_ssh_host=10.210.1.14 ip=10.210.1.14
node5 ansible_ssh_host=10.210.1.15 ip=10.210.1.15

[kube-master]
node2
node3

[etcd]
node2
node3
node4

[kube-node]
node2
node3
node4
node5

[k8s-cluster:children]
kube-node
kube-master

[calico-rr]
rr0
rr1

[rack0]
rr0
rr1
node2
node3
node4
node5

[rack0:vars]
cluster_id="1.0.0.1"
```

The inventory above will deploy the following topology assuming that calico's
`global_as_num` is set to `65400`:

![Image](figures/kargo-calico-rr.png?raw=true)

##### Optional : Define default endpoint to host action

By default Calico blocks traffic from endpoints to the host itself by using an iptables DROP action. When using it in kubernetes the action has to be changed to RETURN (default in kargo) or ACCEPT (see https://github.com/projectcalico/felix/issues/660 and https://github.com/projectcalico/calicoctl/issues/1389). Otherwise all network packets from pods (with hostNetwork=False) to services endpoints (with hostNetwork=True) withing the same node are dropped.


To re-define default action please set the following variable in your inventory:
```
calico_endpoint_to_host_action: "ACCEPT"
```

Cloud providers configuration
=============================

Please refer to the official documentation, for example [GCE configuration](http://docs.projectcalico.org/v1.5/getting-started/docker/installation/gce) requires a security rule for calico ip-ip tunnels. Note, calico is always configured with ``ipip: true`` if the cloud provider was defined.
