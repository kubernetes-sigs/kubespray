# kube-vip

kube-vip provides Kubernetes clusters with a virtual IP and load balancer for both the control plane (for building a highly-available cluster) and Kubernetes Services of type LoadBalancer without relying on any external hardware or software.

## Prerequisites

You have to configure `kube_proxy_strict_arp` when the kube_proxy_mode is `ipvs` and kube-vip ARP is enabled.

```yaml
kube_proxy_strict_arp: true
```

## Install

You have to explicitly enable the kube-vip extension:

```yaml
kube_vip_enabled: true
```

You also need to enable
[kube-vip as HA, Load Balancer, or both](https://kube-vip.io/docs/installation/static/#kube-vip-as-ha-load-balancer-or-both):

```yaml
# HA for control-plane, requires a VIP
kube_vip_controlplane_enabled: true
kube_vip_address: 10.42.42.42
loadbalancer_apiserver:
  address: "{{ kube_vip_address }}"
  port: 6443
# kube_vip_interface: ens160

# LoadBalancer for services
kube_vip_services_enabled: false
# kube_vip_services_interface: ens320
```

> Note: When using `kube-vip` as LoadBalancer for services,
[additional manual steps](https://kube-vip.io/docs/usage/cloud-provider/)
are needed.

If using [local traffic policy](https://kube-vip.io/docs/usage/kubernetes-services/#external-traffic-policy-kube-vip-v050):

```yaml
kube_vip_enableServicesElection: true
```

If using [ARP mode](https://kube-vip.io/docs/installation/static/#arp) :

```yaml
kube_vip_arp_enabled: true
```

If using [BGP mode](https://kube-vip.io/docs/installation/static/#bgp) :

```yaml
kube_vip_bgp_enabled: true
kube_vip_local_as: 65000
kube_vip_bgp_routerid: 192.168.0.2
kube_vip_bgppeers:
- 192.168.0.10:65000::false
- 192.168.0.11:65000::false
# kube_vip_bgp_peeraddress:
# kube_vip_bgp_peerpass:
# kube_vip_bgp_peeras:
```

If using [control plane load-balancing](https://kube-vip.io/docs/about/architecture/#control-plane-load-balancing):

```yaml
kube_vip_lb_enable: true
```
