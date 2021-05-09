# MetalLB

MetalLB hooks into your Kubernetes cluster, and provides a network load-balancer implementation.
In short, it allows you to create Kubernetes services of type "LoadBalancer" in clusters that
don't run on a cloud provider, and thus cannot simply hook into paid products to provide load-balancers.
This addon aims to automate [MetalLB in layer 2 mode](https://metallb.universe.tf/concepts/layer2/)
or [MetalLB in BGP mode](https://metallb.universe.tf/concepts/bgp/).
It deploys MetalLB into Kubernetes and sets up a layer 2 or BGP load-balancer.

## Install

In the default, MetalLB is not deployed into your Kubernetes cluster.
You can override the defaults by copying the contents of roles/kubernetes-apps/metallb/defaults/main.yml
to somewhere in inventory/mycluster/group_vars such as inventory/mycluster/groups_vars/k8s_cluster/addons.yml
and updating `metallb_enabled` option to `true`.
In addition you need to update `metallb_ip_range` option on the addons.yml at least for suiting your network
environment, because MetalLB allocates external IP addresses from this `metallb_ip_range` option.

By default only the MetalLB BGP speaker is allowed to run on control plane nodes. If you have a single node
cluster or a cluster where control plane are also worker nodes you may need to enable tolerations for the
MetalLB controller:

```yaml
metallb_controller_tolerations:
  - key: "node-role.kubernetes.io/master"
    operator: "Equal"
    value: ""
    effect: "NoSchedule"
  - key: "node-role.kubernetes.io/control-plane"
    operator: "Equal"
    value: ""
    effect: "NoSchedule"
```


## BGP Mode

When operating in BGP Mode MetalLB needs to have defined upstream peers:

```yaml
metallb_peers:
  - peer_address: 192.0.2.1
    peer_asn: 64512
    my_asn: 4200000000
  - peer_address: 192.0.2.2
    peer_asn: 64513
    my_asn: 4200000000
```
