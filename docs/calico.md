# Calico

N.B. **Version 2.6.5 upgrade to 3.1.1 is upgrading etcd store to etcdv3**

If you create automated backups of etcdv2 please switch for creating etcdv3 backups, as kubernetes and calico now uses etcdv3
 After migration you can check `/tmp/calico_upgrade/` directory for converted items to etcdv3.
 **PLEASE TEST upgrade before upgrading production cluster.**

Check if the calico-node container is running

```ShellSession
docker ps | grep calico
```

The **calicoctl.sh** is wrap script with configured acces credentials for command calicoctl allows to check the status of the network workloads.

* Check the status of Calico nodes

```ShellSession
calicoctl.sh node status
```

or for versions prior to *v1.0.0*:

```ShellSession
calicoctl.sh status
```

* Show the configured network subnet for containers

```ShellSession
calicoctl.sh get ippool -o wide
```

or for versions prior to *v1.0.0*:

```ShellSession
calicoctl.sh pool show
```

* Show the workloads (ip addresses of containers and their location)

```ShellSession
calicoctl.sh get workloadEndpoint -o wide
```

and

```ShellSession
calicoctl.sh get hostEndpoint -o wide
```

or for versions prior *v1.0.0*:

```ShellSession
calicoctl.sh endpoint show --detail
```

## Configuration

### Optional : Define network backend

In some cases you may want to define Calico network backend. Allowed values are `bird`, `vxlan` or `none`. Bird is a default value.

To re-define you need to edit the inventory and add a group variable `calico_network_backend`

```yml
calico_network_backend: none
```

### Optional : Define the default pool CIDR

By default, `kube_pods_subnet` is used as the IP range CIDR for the default IP Pool.
In some cases you may want to add several pools and not have them considered by Kubernetes as external (which means that they must be within or equal to the range defined in `kube_pods_subnet`), it starts with the default IP Pool of which IP range CIDR can by defined in group_vars (k8s-cluster/k8s-net-calico.yml):

```ShellSession
calico_pool_cidr: 10.233.64.0/20
```

### Optional : BGP Peering with border routers

In some cases you may want to route the pods subnet and so NAT is not needed on the nodes.
For instance if you have a cluster spread on different locations and you want your pods to talk each other no matter where they are located.
The following variables need to be set:
`peer_with_router` to enable the peering with the datacenter's border router (default value: false).
you'll need to edit the inventory and add a hostvar `local_as` by node.

```ShellSession
node1 ansible_ssh_host=95.54.0.12 local_as=xxxxxx
```

### Optional : Defining BGP peers

Peers can be defined using the `peers` variable (see docs/calico_peer_example examples).
In order to define global peers, the `peers` variable can be defined in group_vars with the "scope" attribute of each global peer set to "global".
In order to define peers on a per node basis, the `peers` variable must be defined in hostvars.
NB: Ansible's `hash_behaviour` is by default set to "replace", thus defining both global and per node peers would end up with having only per node peers. If having both global and per node peers defined was meant to happen, global peers would have to be defined in hostvars for each host (as well as per node peers)

Since calico 3.4, Calico supports advertising Kubernetes service cluster IPs over BGP, just as it advertises pod IPs.
This can be enabled by setting the following variable as follow in group_vars (k8s-cluster/k8s-net-calico.yml)

```yml
calico_advertise_cluster_ips: true
```

### Optional : Define global AS number

Optional parameter `global_as_num` defines Calico global AS number (`/calico/bgp/v1/global/as_num` etcd key).
It defaults to "64512".

### Optional : BGP Peering with route reflectors

At large scale you may want to disable full node-to-node mesh in order to
optimize your BGP topology and improve `calico-node` containers' start times.

To do so you can deploy BGP route reflectors and peer `calico-node` with them as
recommended here:

* <https://hub.docker.com/r/calico/routereflector/>
* <https://docs.projectcalico.org/v3.1/reference/private-cloud/l3-interconnect-fabric>

You need to edit your inventory and add:

* `calico-rr` group with nodes in it. `calico-rr` can be combined with
  `kube-node` and/or `kube-master`. `calico-rr` group also must be a child
   group of `k8s-cluster` group.
* `cluster_id` by route reflector node/group (see details
[here](https://hub.docker.com/r/calico/routereflector/))

Here's an example of Kubespray inventory with standalone route reflectors:

```ini
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
calico-rr

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

![Image](figures/kubespray-calico-rr.png?raw=true)

### Optional : Define default endpoint to host action

By default Calico blocks traffic from endpoints to the host itself by using an iptables DROP action. When using it in kubernetes the action has to be changed to RETURN (default in kubespray) or ACCEPT (see <https://github.com/projectcalico/felix/issues/660> and <https://github.com/projectcalico/calicoctl/issues/1389).> Otherwise all network packets from pods (with hostNetwork=False) to services endpoints (with hostNetwork=True) within the same node are dropped.

To re-define default action please set the following variable in your inventory:

```yml
calico_endpoint_to_host_action: "ACCEPT"
```

## Optional : Define address on which Felix will respond to health requests

Since Calico 3.2.0, HealthCheck default behavior changed from listening on all interfaces to just listening on localhost.

To re-define health host please set the following variable in your inventory:

```yml
calico_healthhost: "0.0.0.0"
```

## Config encapsulation for cross server traffic

Calico supports two types of encapsulation: [VXLAN and IP in IP](https://docs.projectcalico.org/v3.11/networking/vxlan-ipip). VXLAN is supported in some environments where IP in IP is not (for example, Azure).

*IP in IP* and *VXLAN* is mutualy exclusive modes.

Configure Ip in Ip mode. Possible values is `Always`, `CrossSubnet`, `Never`.

```yml
calico_ipip_mode: 'Always'
```

Configure VXLAN mode. Possible values is `Always`, `CrossSubnet`, `Never`.

```yml
calico_vxlan_mode: 'Never'
```

If you use VXLAN mode, BGP networking is not required. You can disable BGP to reduce the moving parts in your cluster by `calico_network_backend: vxlan`

## Cloud providers configuration

Please refer to the official documentation, for example [GCE configuration](http://docs.projectcalico.org/v1.5/getting-started/docker/installation/gce) requires a security rule for calico ip-ip tunnels. Note, calico is always configured with ``calico_ipip_mode: Always`` if the cloud provider was defined.

### Optional : Ignore kernel's RPF check setting

By default the felix agent(calico-node) will abort if the Kernel RPF setting is not 'strict'. If you want Calico to ignore the Kernel setting:

```yml
calico_node_ignorelooserpf: true
```

Note that in OpenStack you must allow `ipip` traffic in your security groups,
otherwise you will experience timeouts.
To do this you must add a rule which allows it, for example:

### Optional : Felix configuration via extraenvs of calico node

Possible environment variable parameters for [configuring Felix](https://docs.projectcalico.org/reference/felix/configuration)

```yml
calico_node_extra_envs:
    FELIX_DEVICEROUTESOURCEADDRESS: 172.17.0.1
```

```ShellSession
neutron  security-group-rule-create  --protocol 4  --direction egress  k8s-a0tp4t
neutron  security-group-rule-create  --protocol 4  --direction igress  k8s-a0tp4t
```
