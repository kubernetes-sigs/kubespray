# Calico

Kubespray installs Calico with the [Tigera operator](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises).
For `calico_version`, Kubespray downloads `operator-crds.yaml` and `tigera-operator.yaml` from the Calico release and applies them without changes.
Then it applies an `Installation` resource named `default`, which it makes from the inventory.
The operator deploys `calico-node`, `calico-typha` and `calico-kube-controllers` in the `calico-system` namespace.

Kubespray continues to manage these resources with `calicoctl`: the IP pools, `FelixConfiguration`, `BGPConfiguration`, `BGPPeer`, `IPAMConfig` and the route reflector settings of the nodes.
The operator does not manage IP pools in a Kubespray cluster (`ipPools: []` in the `Installation`).

The Tigera operator supports only the Kubernetes API datastore, so Kubespray does not support the etcd datastore anymore. See [Migrate from the etcd datastore](#migrate-from-the-etcd-datastore).

Check the status of Calico:

```ShellSession
kubectl get tigerastatus
kubectl get pods -n calico-system
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

## Upgrade from the manifest-based install

The first `cluster.yml` or `upgrade_cluster.yml` run with this version moves Calico from the manifests in `kube-system` to the Tigera operator,
with the Calico [operator migration](https://docs.tigera.io/calico/latest/operations/operator-migration).

Requirements:

* Calico uses the Kubernetes API datastore, see [Migrate from the etcd datastore](#migrate-from-the-etcd-datastore).
* `calico_version` has the same minor version as the running Calico.
* `calico-node` is ready on all nodes. With BGP, all BGP peers must be established.
* The nodes can connect to each other on TCP port 5473 (Typha).

If the migration stops, fix the problem and run the playbook again. It continues the migration.

Behavior changes:

* Calico runs in the `calico-system` namespace.
* Calico accepts the traffic from pods to their node (it was `RETURN`), so the firewall rules of the node do not apply to it. Use a Calico host endpoint policy for such rules.
* In eBPF mode, Calico connects to `loadbalancer_apiserver` or to the first control plane node, not to the localhost load balancer.
  For a HA cluster, set `loadbalancer_apiserver` or `calico_kubernetes_service_host`, see [Calico access to the kube-api](#calico-access-to-the-kube-api).

These variables were removed. The playbook stops if your inventory contains them:

| Variable | Replacement |
|----------|-------------|
| `calico_datastore` | none, the Kubernetes API datastore is always used |
| `typha_enabled`, `typha_replicas`, `typha_secure`, `typha_max_connections_lower_limit` | none, the operator manages Typha |
| `calico_node_extra_envs` | `calico_felix_extra_config` for Felix settings |
| `calico_cni_version`, `calico_policy_version`, `calico_typha_version`, `calico_apiserver_version` | `calico_version` |
| `calico_veth_mtu` | `calico_mtu` |
| `calico_felix_log_severity_screen` | `calico_loglevel` |
| `calico_endpoint_to_host_action` | none, the operator uses `ACCEPT` |
| `calico_node_ignorelooserpf` | none, set `net.ipv4.conf.all.rp_filter` to 0 or 1 |
| `calico_crds_download_url` | `calico_operator_crds_download_url` and `calico_operator_manifest_download_url` |
| `calico_feature_control`, `calico_cni_log_file_path`, `calico_ipv4pool_ipip`, `calico_iptables_lock_timeout_secs`, `calico_node_startup_loglevel`, `calico_node_livenessprobe_timeout`, `calico_node_readinessprobe_timeout`, `calico_cert_dir` | none |

## Migrate from the etcd datastore

The Tigera operator supports only the Kubernetes API datastore. Before you upgrade to this version, use the previous Kubespray release (2.32) to move Calico to the Kubernetes API datastore.
The steps follow the Calico document [Migrate Calico data from an etcdv3 datastore to a Kubernetes datastore](https://docs.tigera.io/calico/latest/operations/datastore-migration).
While the datastore is locked, you cannot change the Calico configuration, and new pods do not start.

On the first control plane node:

1. Apply the Calico CRDs of the running Calico version (change `v3.31.7` to it). Kubespray 2.32 applies the same file in step 4:

   ```ShellSession
   kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.31.7/manifests/crds.yaml
   ```

2. Lock the etcd datastore and export it:

   ```ShellSession
   calicoctl.sh datastore migrate lock
   calicoctl.sh datastore migrate export > etcd-data
   ```

3. Import the data into the Kubernetes API datastore:

   ```ShellSession
   DATASTORE_TYPE=kubernetes KUBECONFIG=/etc/kubernetes/admin.conf calicoctl datastore migrate import -f etcd-data
   ```

4. With Kubespray 2.32, run `cluster.yml` with `-e calico_datastore=kdd`. The extra variable is necessary, because Kubespray 2.32 detects the datastore from the CNI configuration. Then wait for the end of the calico-node rollout:

   ```ShellSession
   kubectl -n kube-system rollout status daemonset calico-node
   ```

5. Unlock the datastore:

   ```ShellSession
   DATASTORE_TYPE=kubernetes KUBECONFIG=/etc/kubernetes/admin.conf calicoctl datastore migrate unlock
   ```

Then remove `calico_datastore` from the inventory and upgrade to this version. It moves the cluster to the Tigera operator.

## Configuration

### Optional : Define network backend

In some cases you may want to define Calico network backend. Allowed values are `bird`, `vxlan` or `none`. `vxlan` is the default value.
With `bird`, Kubespray enables BGP in the `Installation`.

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
In order to define peers on a per node basis, the `peers` variable must be defined in hostvars or group_vars with the "scope" attribute unset or set to "node".

NB: Ansible's `hash_behaviour` is by default set to "replace", thus defining both global and per node peers would end up with having only per node peers. If having both global and per node peers defined was meant to happen, global peers would have to be defined in hostvars for each host (as well as per node peers)

NB²: Peers definition at node scope can be customized with additional fields `filters`, `sourceAddress` and `numAllowedLocalASNumbers` (see <https://docs.tigera.io/calico/latest/reference/resources/bgppeer> for details)

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

Optional parameter `global_as_num` defines Calico global AS number (`asNumber` in the `BGPConfiguration`).
It defaults to "64512".

### Optional : BGP Peering with route reflectors

At large scale you may want to disable full node-to-node mesh in order to
optimize your BGP topology and improve `calico-node` containers' start times.

To do so you can deploy BGP route reflectors and peer `calico-node` with them as
recommended here:

* <https://docs.tigera.io/calico/latest/networking/configuring/bgp>

You need to edit your inventory and add:

* `calico_rr` group with nodes in it. `calico_rr` can be combined with
  `kube_node` and/or `kube_control_plane`.
* `cluster_id` by route reflector node/group

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

![Image](../figures/kubespray-calico-rr.png?raw=true)

### Optional : Define address on which Felix will respond to health requests

Since Calico 3.2.0, HealthCheck default behavior changed from listening on all interfaces to just listening on localhost.
The probes of the operator use localhost, so the address must include it.

To re-define health host please set the following variable in your inventory:

```yml
calico_healthhost: "0.0.0.0"
```

### Optional : Configure VXLAN hardware Offload

The VXLAN Offload is disable by default. It can be configured like this to enabled it:

```yml
calico_feature_detect_override: "ChecksumOffloadBroken=false" # The vxlan offload will enabled (It may cause problem on buggy NIC driver)
```

### Optional :  Enable NAT with IPv6

To allow outgoing IPv6 traffic going from pods to the Internet, enable the following:

```yml
nat_outgoing_ipv6: true  # NAT outgoing ipv6 (default value: false).
```

### Optional : Felix configuration

Kubespray sets the fields of the `FelixConfiguration` named `default` that its variables control. You can set more fields with `calico_felix_extra_config`,
see [Felix configuration](https://docs.tigera.io/calico/latest/reference/resources/felixconfig).
The operator sets `bpfEnabled` and `nftablesMode`, so use `calico_bpf_enabled` and `calico_nftable_mode` for them.

```yml
calico_felix_extra_config:
  bpfConnectTimeLoadBalancing: TCP
```

### Optional : Installation configuration

You can set more fields of the `Installation` with `calico_operator_installation_spec`. Kubespray merges it over the values that it sets,
see [Installation reference](https://docs.tigera.io/calico/latest/reference/installation/api).

```yml
calico_operator_installation_spec:
  controlPlaneReplicas: 1
```

### Optional : Use Calico CNI host-local IPAM plugin

Calico currently supports two types of CNI IPAM plugins, `host-local` and `calico-ipam` (default).

To allow Calico to determine the subnet to use from the Kubernetes API based on the `Node.podCIDR` field, enable the following setting.
The operator does not support VXLAN with host-local IPAM.

```yml
calico_ipam_host_local: true
```

Refer to Project Calico section [Using host-local IPAM](https://docs.tigera.io/calico/latest/reference/configure-cni-plugins#using-host-local-ipam) for further information.

## Config encapsulation for cross server traffic

Calico supports two types of encapsulation: [VXLAN and IP in IP](https://docs.tigera.io/calico/latest/networking/configuring/vxlan-ipip). VXLAN is the more mature implementation and enabled by default, please check your environment if you need *IP in IP* encapsulation.

*IP in IP* and *VXLAN* is mutually exclusive modes.

**Note:**: Vxlan in ipv6 only supported when kernel >= 3.12. So if your kernel version < 3.12, Please don't set `calico_vxlan_mode_ipv6: Always`. More details see [#Issue 6877](https://github.com/projectcalico/calico/issues/6877).

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

This is an advanced topic and should usually not be modified unless you know exactly what you are doing. Calico is smart enough to deal with the defaults and calculate the proper MTU. If you do need to set up a custom MTU you can change `calico_mtu` as follows.
The operator uses the same MTU for the workload interfaces and the tunnels.

* If Wireguard is enabled, subtract 60 from your network MTU (i.e. 1500-60=1440)
* If using VXLAN or BPF mode is enabled, subtract 50 from your network MTU (i.e. 1500-50=1450)
* If using IPIP, subtract 20 from your network MTU (i.e. 1500-20=1480)
* if not using any encapsulation, set to your network MTU (i.e. 1500 or 9000)

```yaml
calico_mtu: 1440
```

## Cloud providers configuration

Please refer to the official documentation, for example [GCE configuration](http://docs.projectcalico.org/v1.5/getting-started/docker/installation/gce) requires a security rule for calico ip-ip tunnels.

Note that in OpenStack you must allow `ipip` traffic in your security groups,
otherwise you will experience timeouts.
To do this you must add a rule which allows it, for example:

```ShellSession
neutron  security-group-rule-create  --protocol 4  --direction egress  k8s-a0tp4t
neutron  security-group-rule-create  --protocol 4  --direction igress  k8s-a0tp4t
```

## Offline environment

The Tigera operator manifest always pulls `quay.io/tigera/operator`. Kubespray does not download this image, so the image list of `contrib/offline` does not contain it.
Copy the image that `tigera-operator.yaml` names to your registry. In an offline environment, configure a containerd registry mirror for `quay.io`, for example:

```yaml
containerd_registries_mirrors:
  - prefix: quay.io
    mirrors:
      - host: https://myprivateregistry.com
        capabilities: ["pull", "resolve"]
        skip_verify: false
```

The operator pulls the Calico images from `quay_image_repo`. Set `calico_operator_crds_download_url` and `calico_operator_manifest_download_url` to your file server,
see the sample [offline.yml](/inventory/sample/group_vars/all/offline.yml).

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

Without kube-proxy, the Calico pods cannot use the `kubernetes` Service to connect to the API server.
Kubespray writes the `kubernetes-services-endpoint` ConfigMap in the `tigera-operator` namespace with an address that the pods can reach:
`loadbalancer_apiserver` if it is defined, else the first control plane node.
Set `calico_kubernetes_service_host` and `calico_kubernetes_service_port` to use another address.
Calico [requires a load balancer for a HA set-up](https://docs.tigera.io/calico/latest/operations/ebpf/enabling-ebpf), so do not use the first control plane node in a HA cluster.
See also the [Enabling eBPF Calico Docs](https://docs.tigera.io/calico/latest/operations/ebpf/enabling-ebpf).

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

Please see [Calico eBPF troubleshooting guide](https://docs.tigera.io/calico/latest/operations/ebpf/troubleshoot-ebpf).

## Wireguard Encryption

Calico supports using Wireguard for encryption. Please see the docs on [encrypt cluster pod traffic](https://docs.tigera.io/calico/latest/network-policy/encrypt-cluster-pod-traffic).

To enable wireguard support:

```yaml
calico_wireguard_enabled: true
```

The following OSes will require enabling the EPEL repo in order to bring in wireguard tools:

* CentOS 8
* AlmaLinux 8
* Rocky Linux 8
* Amazon Linux 2

```yaml
epel_enabled: true
```
