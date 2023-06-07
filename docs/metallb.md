# MetalLB

MetalLB hooks into your Kubernetes cluster, and provides a network load-balancer implementation.
It allows you to create Kubernetes services of type "LoadBalancer" in clusters that don't run on a cloud provider, and thus cannot simply hook into 3rd party products to provide load-balancers.
The default operating mode of MetalLB is in ["Layer2"](https://metallb.universe.tf/concepts/layer2/) but it can also operate in ["BGP"](https://metallb.universe.tf/concepts/bgp/) mode.

## Prerequisites

You have to configure arp_ignore and arp_announce to avoid answering ARP queries from kube-ipvs0 interface for MetalLB to work.

```yaml
kube_proxy_strict_arp: true
```

## Install

You have to explicitly enable the MetalLB extension.

```yaml
metallb_enabled: true
metallb_speaker_enabled: true
```

By default only the MetalLB BGP speaker is allowed to run on control plane nodes. If you have a single node cluster or a cluster where control plane are also worker nodes you may need to enable tolerations for the MetalLB controller:

```yaml
metallb_config:
  controller:
    nodeselector:
      kubernetes.io/os: linux
    tolerations:
    - key: "node-role.kubernetes.io/master"
      operator: "Equal"
      value: ""
      effect: "NoSchedule"
    - key: "node-role.kubernetes.io/control-plane"
      operator: "Equal"
      value: ""
      effect: "NoSchedule"
```

If you'd like to set additional nodeSelector and tolerations values, you can do so in the following fasion:

```yaml
metallb_config:
  controller:
    nodeselector:
      kubernetes.io/os: linux
    tolerations:
    - key: "node-role.kubernetes.io/control-plane"
      operator: "Equal"
      value: ""
      effect: "NoSchedule"
  speaker:
    nodeselector:
      kubernetes.io/os: linux
    tolerations:
    - key: "node-role.kubernetes.io/control-plane"
      operator: "Equal"
      value: ""
      effect: "NoSchedule"
```

## Pools

First you need to specify all of the pools you are going to use:

```yaml
metallb_config:

  address_pools:

    primary:
      ip_range:
        - 192.0.1.0-192.0.1.254
      auto_assign: true

    pool1:
      ip_range:
        - 192.0.2.1-192.0.2.1
      auto_assign: false # When set to false, you need to explicitly set the loadBalancerIP in the service!

    pool2:
      ip_range:
        - 192.0.2.2-192.0.2.2
      auto_assign: false
```

## Layer2 Mode

Pools that need to be configured in layer2 mode, need to be specified in a list:

```yaml
metallb_config:

  layer2:
    - primary
```

## BGP Mode

When operating in BGP Mode MetalLB needs to have defined upstream peers and link the pool(s) specified above to the correct peer:

```yaml
metallb_config:

  layer3:
    defaults:

      peer_port: 179 # The TCP port to talk to. Defaults to 179, you shouldn't need to set this in production.
      hold_time: 120s # Requested BGP hold time, per RFC4271.

    communities:
      vpn-only: "1234:1"
      NO_ADVERTISE: "65535:65282"

    metallb_peers:

        peer1:
          peer_address: 192.0.2.1
          peer_asn: 64512
          my_asn: 4200000000
          communities:
            - vpn-only
          address_pool:
            - pool1

          # (optional) The source IP address to use when establishing the BGP session. In most cases the source-address field should only be used with per-node peers, i.e. peers with node selectors which select only one node. CURRENTLY NOT SUPPORTED
          source_address: 192.0.2.2

          # (optional) The router ID to use when connecting to this peer. Defaults to the node IP address.
          # Generally only useful when you need to peer with another BGP router running on the same machine as MetalLB.
          router_id: 1.2.3.4

          # (optional) Password for TCPMD5 authenticated BGP sessions offered by some peers.
          password: "changeme"

        peer2:
          peer_address: 192.0.2.2
          peer_asn: 64513
          my_asn: 4200000000
          communities:
            - NO_ADVERTISE
          address_pool:
            - pool2

          # (optional) The source IP address to use when establishing the BGP session. In most cases the source-address field should only be used with per-node peers, i.e. peers with node selectors which select only one node. CURRENTLY NOT SUPPORTED
          source_address: 192.0.2.1

          # (optional) The router ID to use when connecting to this peer. Defaults to the node IP address.
          # Generally only useful when you need to peer with another BGP router running on the same machine as MetalLB.
          router_id: 1.2.3.5

          # (optional) Password for TCPMD5 authenticated BGP sessions offered by some peers.
          password: "changeme"
```

When using calico >= 3.18 you can replace MetalLB speaker by calico Service LoadBalancer IP advertisement.
See [calico service IPs advertisement documentation](https://docs.projectcalico.org/archive/v3.18/networking/advertise-service-ips#advertise-service-load-balancer-ip-addresses).
In this scenario you should disable the MetalLB speaker and configure the `calico_advertise_service_loadbalancer_ips` to match your `ip_range`

```yaml
metallb_speaker_enabled: false
metallb_config:
  address_pools:
    primary:
      ip_range:
        - 10.5.0.0/16
      auto_assign: true
  layer2:
    - primary
calico_advertise_service_loadbalancer_ips: "{{ metallb_config.address_pools.primary.ip_range }}"
```

If you have additional loadbalancer IP pool in `metallb_config.address_pools` , ensure to add them to the list.

```yaml
metallb_speaker_enabled: false
metallb_config:
  address_pools:
    primary:
      ip_range:
        - 10.5.0.0/16
      auto_assign: true
    pool1:
      ip_range:
        - 10.6.0.0/16
      auto_assign: true
    pool2:
      ip_range:
        - 10.10.0.0/16
      auto_assign: true
  layer2:
    - primary
  layer3:
    defaults:
      peer_port: 179
      hold_time: 120s
    communities:
      vpn-only: "1234:1"
      NO_ADVERTISE: "65535:65282"
    metallb_peers:
      peer1:
        peer_address: 10.6.0.1
        peer_asn: 64512
        my_asn: 4200000000
        communities:
          - vpn-only
        address_pool:
          - pool1
      peer2:
        peer_address: 10.10.0.1
        peer_asn: 64513
        my_asn: 4200000000
        communities:
          - NO_ADVERTISE
        address_pool:
          - pool2
calico_advertise_service_loadbalancer_ips:
  - 10.5.0.0/16
  - 10.6.0.0/16
  - 10.10.0.0/16
```
