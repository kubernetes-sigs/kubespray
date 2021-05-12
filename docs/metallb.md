# MetalLB

MetalLB hooks into your Kubernetes cluster, and provides a network load-balancer implementation.
It allows you to create Kubernetes services of type "LoadBalancer" in clusters that don't run on a cloud provider, and thus cannot simply hook into 3rd party products to provide load-balancers.
The default operationg mode of MetalLB is in ["Layer2"](https://metallb.universe.tf/concepts/layer2/) but it can also operate in ["BGP"](https://metallb.universe.tf/concepts/bgp/) mode.

## Install

You have to explicitly enable the MetalLB extension and set an IP address range from which to allocate LoadBalancer IPs.

```yaml
metallb_enabled: true
metallb_speaker_enabled: true
metallb_ip_range:
  - 10.5.0.0/16
```

By default only the MetalLB BGP speaker is allowed to run on control plane nodes. If you have a single node cluster or a cluster where control plane are also worker nodes you may need to enable tolerations for the MetalLB controller:

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
metallb_protocol: bgp
metallb_ip_range:
  - 10.5.0.0/16
metallb_peers:
  - peer_address: 192.0.2.1
    peer_asn: 64512
    my_asn: 4200000000
  - peer_address: 192.0.2.2
    peer_asn: 64513
    my_asn: 4200000000
```

When using calico >= 3.18 you can replace MetalLB speaker by calico Service LoadBalancer IP advertisement.
See [calico service IPs advertisement documentation](https://docs.projectcalico.org/archive/v3.18/networking/advertise-service-ips#advertise-service-load-balancer-ip-addresses).
In this scenarion you should disable the MetalLB speaker and configure the `calico_advertise_service_loadbalancer_ips` to match your `metallb_ip_range`

```yaml
metallb_speaker_enabled: false
metallb_ip_range:
  - 10.5.0.0/16
calico_advertise_service_loadbalancer_ips: "{{ metallb_ip_range }}"
```

If you have additional loadbalancer IP pool in `metallb_additional_address_pools`, ensure to add them to the list.

```yaml
metallb_speaker_enabled: false
metallb_ip_range:
  - 10.5.0.0/16
metallb_additional_address_pools:
  kube_service_pool_1:
    ip_range:
      - 10.6.0.0/16
    protocol: "bgp"
    auto_assign: false
  kube_service_pool_2:
    ip_range:
      - 10.10.0.0/16
    protocol: "bgp"
    auto_assign: false
calico_advertise_service_loadbalancer_ips:
  - 10.5.0.0/16
  - 10.6.0.0/16
  - 10.10.0.0/16
```
