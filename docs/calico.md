# Calico

Check if the calico-node container is running

```ShellSession
docker ps | grep calico
```

The **calicoctl.sh** is wrap script with configured access credentials for command calicoctl allows to check the status of the network workloads.

* Check the status of Calico nodes

```ShellSession
calicoctl.sh node status
```

* Show the configured network subnet for containers

```ShellSession
calicoctl.sh get ippool -o wide
```

* Show the workloads (ip addresses of containers and their location)

```ShellSession
calicoctl.sh get workloadEndpoint -o wide
```

and

```ShellSession
calicoctl.sh get hostEndpoint -o wide
```

## Configuration

### Optional : Define datastore type

The default datastore, Kubernetes API datastore is recommended for on-premises deployments, and supports only Kubernetes workloads; etcd is the best datastore for hybrid deployments.

Allowed values are `kdd` (default) and `etcd`.

Note: using kdd and more than 50 nodes, consider using the `typha` daemon to provide scaling.

To re-define you need to edit the inventory and add a group variable `calico_datastore`

```yml
calico_datastore: kdd
```

### Optional : Define network backend

In some cases you may want to define Calico network backend. Allowed values are `bird`, `vxlan` or `none`. `vxlan` is the default value.

To re-define you need to edit the inventory and add a group variable `calico_network_backend`

```yml
calico_network_backend: none
```

### Optional : Define the default pool CIDRs

By default, `kube_pods_subnet` is used as the IP range CIDR for the default IP Pool, and `kube_pods_subnet_ipv6` for IPv6.
In some cases you may want to add several pools and not have them considered by Kubernetes as external (which means that they must be within or equal to the range defined in `kube_pods_subnet` and `kube_pods_subnet_ipv6` ), it starts with the default IP Pools of which IP range CIDRs can by defined in group_vars (k8s_cluster/k8s-net-calico.yml):

```ShellSession
calico_pool_cidr: 10.233.64.0/20
calico_pool_cidr_ipv6: fd85:ee78:d8a6:8607::1:0000/112
```

### Optional : BGP Peering with border routers

In some cases you may want to route the pods subnet and so NAT is not needed on the nodes.
For instance if you have a cluster spread on different locations and you want your pods to talk each other no matter where they are located.
The following variables need to be set as follow:

```yml
peer_with_router: true  # enable the peering with the datacenter's border router (default value: false).
nat_outgoing: false  # (optional) NAT outgoing (default value: true).
```

And you'll need to edit the inventory and add a hostvar `local_as` by node.

```ShellSession
node1 ansible_ssh_host=95.54.0.12 local_as=xxxxxx
```

### Optional : Defining BGP peers

Peers can be defined using the `peers` variable (see docs/calico_peer_example examples).
In order to define global peers, the `peers` variable can be defined in group_vars with the "scope" attribute of each global peer set to "global".
In order to define peers on a per node basis, the `peers` variable must be defined in hostvars.
NB: Ansible's `hash_behaviour` is by default set to "replace", thus defining both global and per node peers would end up with having only per node peers. If having both global and per node peers defined was meant to happen, global peers would have to be defined in hostvars for each host (as well as per node peers)

Since calico 3.4, Calico supports advertising Kubernetes service cluster IPs over BGP, just as it advertises pod IPs.
This can be enabled by setting the following variable as follow in group_vars (k8s_cluster/k8s-net-calico.yml)

```yml
calico_advertise_cluster_ips: true
```

Since calico 3.10, Calico supports advertising Kubernetes service ExternalIPs over BGP in addition to cluster IPs advertising.
This can be enabled by setting the following variable in group_vars (k8s_cluster/k8s-net-calico.yml)

```yml
calico_advertise_service_external_ips:
- x.x.x.x/24
- y.y.y.y/32
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

* `calico_rr` group with nodes in it. `calico_rr` can be combined with
  `kube_node` and/or `kube_control_plane`. `calico_rr` group also must be a child
   group of `k8s_cluster` group.
* `cluster_id` by route reflector node/group (see details [here](https://hub.docker.com/r/calico/routereflector/))

Here's an example of Kubespray inventory with standalone route reflectors:

```ini
[all]
rr0 ansible_ssh_host=10.210.1.10 ip=10.210.1.10
rr1 ansible_ssh_host=10.210.1.11 ip=10.210.1.11
node2 ansible_ssh_host=10.210.1.12 ip=10.210.1.12
node3 ansible_ssh_host=10.210.1.13 ip=10.210.1.13
node4 ansible_ssh_host=10.210.1.14 ip=10.210.1.14
node5 ansible_ssh_host=10.210.1.15 ip=10.210.1.15

[kube_control_plane]
node2
node3

[etcd]
node2
node3
node4

[kube_node]
node2
node3
node4
node5

[k8s_cluster:children]
kube_node
kube_control_plane
calico_rr

[calico_rr]
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
calico_rr_id=rr1
calico_group_id=rr1
```

The inventory above will deploy the following topology assuming that calico's
`global_as_num` is set to `65400`:

![Image](figures/kubespray-calico-rr.png?raw=true)

### Optional : Define default endpoint to host action

By default Calico blocks traffic from endpoints to the host itself by using an iptables DROP action. When using it in kubernetes the action has to be changed to RETURN (default in kubespray) or ACCEPT (see <https://docs.tigera.io/calico/latest/network-policy/hosts/protect-hosts#control-default-behavior-of-workload-endpoint-to-host-traffic> ) Otherwise all network packets from pods (with hostNetwork=False) to services endpoints (with hostNetwork=True) within the same node are dropped.

To re-define default action please set the following variable in your inventory:

```yml
calico_endpoint_to_host_action: "ACCEPT"
```

### Optional : Define address on which Felix will respond to health requests

Since Calico 3.2.0, HealthCheck default behavior changed from listening on all interfaces to just listening on localhost.

To re-define health host please set the following variable in your inventory:

```yml
calico_healthhost: "0.0.0.0"
```

### Optional : Configure VXLAN hardware Offload

The VXLAN Offload is disable by default. It can be configured like this to enabled it:

```yml
calico_feature_detect_override: "ChecksumOffloadBroken=false" # The vxlan offload will enabled (It may cause problem on buggy NIC driver)
```

### Optional : Configure Calico Node probe timeouts

Under certain conditions a deployer may need to tune the Calico liveness and readiness probes timeout settings. These can be configured like this:

```yml
calico_node_livenessprobe_timeout: 10
calico_node_readinessprobe_timeout: 10
```

## Config encapsulation for cross server traffic

Calico supports two types of encapsulation: [VXLAN and IP in IP](https://docs.projectcalico.org/v3.11/networking/vxlan-ipip). VXLAN is the more mature implementation and enabled by default, please check your environment if you need *IP in IP* encapsulation.

*IP in IP* and *VXLAN* is mutually exclusive modes.

Kubespray defaults have changed after version 2.18 from auto-enabling `ipip` mode to auto-enabling `vxlan`. This was done to facilitate wider deployment scenarios including those where vxlan acceleration is provided by the underlying network devices.

If you are running your cluster with the default calico settings and are upgrading to a release post 2.18.x (i.e. 2.19 and later or `master` branch) then you have two options:

* perform a manual migration to vxlan before upgrading kubespray (see migrating from IP in IP to VXLAN below)
* pin the pre-2.19 settings in your ansible inventory (see IP in IP mode settings below)

**Note:**: Vxlan in ipv6 only supported when kernel >= 3.12. So if your kernel version < 3.12, Please don't set `calico_vxlan_mode_ipv6: vxlanAlways`. More details see [#Issue 6877](https://github.com/projectcalico/calico/issues/6877).

### IP in IP mode

To configure Ip in Ip mode you need to use the bird network backend.

```yml
calico_ipip_mode: 'Always'  # Possible values is `Always`, `CrossSubnet`, `Never`
calico_vxlan_mode: 'Never'
calico_network_backend: 'bird'
```

### BGP mode

To enable BGP no-encapsulation mode:

```yml
calico_ipip_mode: 'Never'
calico_vxlan_mode: 'Never'
calico_network_backend: 'bird'
```

### Migrating from IP in IP to VXLAN

If you would like to migrate from the old IP in IP with `bird` network backends default to the new VXLAN based encapsulation you need to perform this change before running an upgrade of your cluster; the `cluster.yml` and `upgrade-cluster.yml` playbooks will refuse to continue if they detect incompatible settings.

Execute the following steps on one of the control plane nodes, ensure the cluster in healthy before proceeding.

```shell
calicoctl.sh patch felixconfig default -p '{"spec":{"vxlanEnabled":true}}'
calicoctl.sh patch ippool default-pool -p '{"spec":{"ipipMode":"Never", "vxlanMode":"Always"}}'
```

**Note:** if you created multiple ippools you will need to patch all of them individually to change their encapsulation. The kubespray playbooks only handle the default ippool created by kubespray.

Wait for the `vxlan.calico` interfaces to be created on all cluster nodes and traffic to be routed through it then you can disable `ipip`.

```shell
calicoctl.sh patch felixconfig default -p '{"spec":{"ipipEnabled":false}}'
```

## Configuring interface MTU

This is an advanced topic and should usually not be modified unless you know exactly what you are doing. Calico is smart enough to deal with the defaults and calculate the proper MTU. If you do need to set up a custom MTU you can change `calico_veth_mtu` as follows:

* If Wireguard is enabled, subtract 60 from your network MTU (i.e. 1500-60=1440)
* If using VXLAN or BPF mode is enabled, subtract 50 from your network MTU (i.e. 1500-50=1450)
* If using IPIP, subtract 20 from your network MTU (i.e. 1500-20=1480)
* if not using any encapsulation, set to your network MTU (i.e. 1500 or 9000)

```yaml
calico_veth_mtu: 1440
```

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

### Optional : Use Calico CNI host-local IPAM plugin

Calico currently supports two types of CNI IPAM plugins, `host-local` and `calico-ipam` (default).

To allow Calico to determine the subnet to use from the Kubernetes API based on the `Node.podCIDR` field, enable the following setting.

```yml
calico_ipam_host_local: true
```

Refer to Project Calico section [Using host-local IPAM](https://docs.projectcalico.org/reference/cni-plugin/configuration#using-host-local-ipam) for further information.

### Optional : Disable CNI logging to disk

Calico CNI plugin logs to /var/log/calico/cni/cni.log and to stderr.
stderr of CNI plugins can be found in the logs of container runtime.

You can disable Calico CNI logging to disk by setting `calico_cni_log_file_path: false`.

## eBPF Support

Calico supports eBPF for its data plane see [an introduction to the Calico eBPF Dataplane](https://www.projectcalico.org/introducing-the-calico-ebpf-dataplane/) for further information.

Note that it is advisable to always use the latest version of Calico when using the eBPF dataplane.

### Enabling eBPF support

To enable the eBPF dataplane support ensure you add the following to your inventory. Note that the `kube-proxy` is incompatible with running Calico in eBPF mode and the kube-proxy should be removed from the system.

```yaml
calico_bpf_enabled: true
```

**NOTE:** there is known incompatibility in using the `kernel-kvm` kernel package on Ubuntu OSes because it is missing support for `CONFIG_NET_SCHED` which is a requirement for Calico eBPF support. When using Calico eBPF with Ubuntu ensure you run the `-generic` kernel.

### Cleaning up after kube-proxy

Calico node cannot clean up after kube-proxy has run in ipvs mode. If you are converting an existing cluster to eBPF you will need to ensure the `kube-proxy` DaemonSet is deleted and that ipvs rules are cleaned.

To check that kube-proxy was running in ipvs mode:

```ShellSession
# ipvsadm -l
```

To clean up any ipvs leftovers:

```ShellSession
# ipvsadm -C
```

### Calico access to the kube-api

Calico node, typha and kube-controllers need to be able to talk to the kubernetes API. Please reference the [Enabling eBPF Calico Docs](https://docs.projectcalico.org/maintenance/ebpf/enabling-bpf) for guidelines on how to do this.

Kubespray sets up the `kubernetes-services-endpoint` configmap based on the contents of the `loadbalancer_apiserver` inventory variable documented in [HA Mode](/docs/ha-mode.md).

If no external loadbalancer is used, Calico eBPF can also use the localhost loadbalancer option. We are able to do so only if you use the same port for the localhost apiserver loadbalancer and the kube-apiserver. In this case Calico Automatic Host Endpoints need to be enabled to allow services like `coredns` and `metrics-server` to communicate with the kubernetes host endpoint. See [this blog post](https://www.projectcalico.org/securing-kubernetes-nodes-with-calico-automatic-host-endpoints/) on enabling automatic host endpoints.

### Tunneled versus Direct Server Return

By default Calico uses Tunneled service mode but it can use direct server return (DSR) in order to optimize the return path for a service.

To configure DSR:

```yaml
calico_bpf_service_mode: "DSR"
```

### eBPF Logging and Troubleshooting

In order to enable Calico eBPF mode logging:

```yaml
calico_bpf_log_level: "Debug"
```

To view the logs you need to use the `tc` command to read the kernel trace buffer:

```ShellSession
tc exec bpf debug
```

Please see [Calico eBPF troubleshooting guide](https://docs.projectcalico.org/maintenance/troubleshoot/troubleshoot-ebpf#ebpf-program-debug-logs).

## Wireguard Encryption

Calico supports using Wireguard for encryption. Please see the docs on [encrypt cluster pod traffic](https://docs.projectcalico.org/security/encrypt-cluster-pod-traffic).

To enable wireguard support:

```yaml
calico_wireguard_enabled: true
```

The following OSes will require enabling the EPEL repo in order to bring in wireguard tools:

* CentOS 7 & 8
* AlmaLinux 8
* Rocky Linux 8
* Amazon Linux 2

```yaml
epel_enabled: true
```
