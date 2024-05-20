# Port Requirements

To operate properly, Kubespray requires some ports to be opened. If the network is configured with firewall rules, it is needed to ensure infrastructure components can communicate with each other through specific ports.

Ensure the following ports required by Kubespray are open on the network and configured to allow access between hosts. Some ports are optional depending on the configuration and usage.

## Kubernetes

### Control plane

| Protocol | Port   | Description     |
|----------|--------| ------------    |
| TCP      | 22     | ssh for ansible |
| TCP      | 2379   | etcd client port|
| TCP      | 2380   | etcd peer port  |
| TCP      | 6443   | kubernetes api  |
| TCP      | 10250  | kubelet api     |
| TCP      | 10257  | kube-scheduler  |
| TCP      | 10259  | kube-controller-manager  |

### Worker node(s)

| Protocol | Port       | Description     |
|----------|--------    | ------------    |
| TCP      | 22         | ssh for ansible |
| TCP      | 10250      | kubelet api     |
| TCP      | 30000-32767| kube nodePort range |

refers to: [Kubernetes Docs](https://kubernetes.io/docs/reference/networking/ports-and-protocols/)

## Calico

If Calico is used, it requires:

| Protocol | Port       | Description   |
|----------|--------    | ------------  |
| TCP      | 179        | Calico networking (BGP) |
| UDP      | 4789       | Calico CNI with VXLAN enabled |
| TCP      | 5473       | Calico CNI with Typha enabled  |
| UDP      | 51820      | Calico with IPv4 Wireguard enabled |
| UDP      | 51821      | Calico with IPv6 Wireguard enabled |
| IPENCAP / IPIP | -    | Calico CNI with IPIP enabled  |

refers to: [Calico Docs](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements#network-requirements)

## Cilium

If Cilium is used, it requires:

| Protocol | Port     | Description   |
|----------|--------  | ------------  |
| TCP      | 4240     | Cilium Health checks (``cilium-health``)  |
| TCP      | 4244     | Hubble server  |
| TCP      | 4245     | Hubble Relay  |
| UDP      | 8472     | VXLAN overlay  |
| TCP      | 9962     | Cilium-agent Prometheus metrics  |
| TCP      | 9963     | Cilium-operator Prometheus metrics  |
| TCP      | 9964     | Cilium-proxy Prometheus metrics  |
| UDP      | 51871    | WireGuard encryption tunnel endpoint  |
| ICMP     | -        | health checks  |

refers to: [Cilium Docs](https://docs.cilium.io/en/v1.13/operations/system_requirements/)

## Addons

| Protocol | Port       | Description   |
|----------|--------    | ------------  |
| TCP      | 9100       | node exporter |
| TCP/UDP  | 7472       | metallb metrics ports |
| TCP/UDP  | 7946       | metallb L2 operating mode |
