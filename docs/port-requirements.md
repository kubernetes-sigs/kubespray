# Port Requirements

To operate properly, KubeSpray requires some ports to be opened. If the network is configured with firewall rules, it is needed to ensure infrastructure components can communicate with each other through specific ports.

Ensure the following ports required by KubeSpray are open on the network and configured to allow access between hosts. Some ports are optional depending on the configuration and usage.

## Control Plane in Cluster

| Protocol | Port   | Description |
|----------|--------| ------------|
| TCP	   | 2379	| etcd client port|
| TCP	   | 2380	| etcd peer port |
| TCP	   | 6443	| kube api |
| TCP	   | 10250-10258 | kube control plane components |

## All Node in Cluster

## Kube

| Protocol | Port       | Description   |
|----------|--------    | ------------  |
| TCP	   | 22	        | ssh for ansible |
| TCP	   | 10250	    | kubelet       |
| TCP	   | 10256	    | kube-proxy    |
| TCP	   | 30000-32767| kube NodePort Range |

## Calico

If Calico is be used, it requries:

| Protocol | Port       | Description   |
|----------|--------    | ------------  |
| TCP      | 179        | Calico networking (BGP)	|
| UDP	   | 4789	    | Calico CNI with VXLAN enabled |
| TCP 	   | 5473 	    | Calico CNI with Typha enabled  |
| IPENCAP / IPIP | -    | Calico CNI with IPIP enabled  |


refers to: https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements#network-requirements

## Cilium 

If Cilium  is be used, it requries:

| Protocol | Port       | Description   |
|----------|--------    | ------------  |
| UDP	   | 8472	    | Cilium CNI with VXLAN  |

refers to: https://docs.cilium.io/en/v1.13/operations/system_requirements/


## Addons
| Protocol | Port       | Description   |
|----------|--------    | ------------  |
| TCP	   | 9100	    | node exporter |
| TCP/UDP  | 7472       | metallb metrics ports |
| TCP/UDP  | 7946       | metallb L2 operating mode |

