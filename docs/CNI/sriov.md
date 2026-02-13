# SR-IOV Network Operator

**Note:** SR-IOV support is not currently covered in kubespray CI and
support for it is currently considered experimental.

The [SR-IOV Network Operator](https://github.com/k8snetworkplumbingwg/sriov-network-operator) manages SR-IOV network devices and network attachments in Kubernetes. Kubespray deploys it via the upstream Helm chart.

## Requirements

SR-IOV requires Multus and physical NICs that support SR-IOV (Intel X710/E810, Mellanox ConnectX-4/5/6, etc.). IOMMU must be enabled in BIOS and kernel boot parameters (`intel_iommu=on` or `amd_iommu=on`).

## Installation

Enable both Multus and SR-IOV in your inventory:

```yml
kube_network_plugin_multus: true
kube_network_plugin_sriov: true
```

To customize configuration, copy the sample file:

```ShellSession
cp inventory/sample/group_vars/k8s_cluster/k8s-net-sriov.yml \
   inventory/mycluster/group_vars/k8s_cluster/
```

See `roles/network_plugin/sriov/defaults/main.yml` for all available variables.

Deploy as usual:

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.ini cluster.yml
```

Or deploy only SR-IOV:

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.ini cluster.yml --tags sriov
```

### Verify the deployment

```ShellSession
kubectl get pods -n sriov-network-operator
```

The operator pod and config daemon should be Running. On nodes with SR-IOV hardware, the operator automatically discovers available devices:

```ShellSession
kubectl get sriovnetworknodestates -n sriov-network-operator
kubectl get sriovnetworknodestate <node-name> -n sriov-network-operator -o yaml
```

## Configuration

### Disable node draining

For single-node or development clusters where draining is not possible:

```yml
sriov_operator_disable_drain: true
```

### Resource prefix

The default resource prefix is `openshift.io` (upstream default). Pods request SR-IOV VFs using this prefix, e.g. `openshift.io/intel_sriov_netdevice: '1'`.

```yml
sriov_operator_resource_prefix: "openshift.io"
```

### Admission controller

The operator includes an optional webhook for validating SR-IOV CRs. Disabled by default:

```yml
sriov_operator_enable_admission_controller: true
```

### Prometheus metrics

```yml
sriov_operator_enable_prometheus: true
```

### Extra Helm values

For chart values not exposed as Kubespray variables:

```yml
sriov_operator_extra_values:
  supportedExtraNICs: ["myNIC"]
```

## Usage

After the operator is deployed, SR-IOV is configured through Kubernetes CRs. Label nodes that have SR-IOV NICs first:

```ShellSession
kubectl label node <node-name> feature.node.kubernetes.io/network-sriov.capable=true
```

### Create a SriovNetworkNodePolicy

This tells the operator how to configure VFs on matching nodes:

```yaml
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetworkNodePolicy
metadata:
  name: policy-intel-nic
  namespace: sriov-network-operator
spec:
  nodeSelector:
    feature.node.kubernetes.io/network-sriov.capable: "true"
  resourceName: intel_sriov_netdevice
  priority: 99
  numVfs: 8
  mtu: 1500
  nicSelector:
    pfNames: ["ens1f0"]
  deviceType: netdevice
```

Apply and watch progress:

```ShellSession
kubectl apply -f sriov-policy.yaml
kubectl get sriovnetworknodestates -n sriov-network-operator -w
```

The config daemon will drain nodes before reconfiguring NICs (unless `sriov_operator_disable_drain: true`).

### Create a SriovNetwork

This automatically generates a Multus NetworkAttachmentDefinition:

```yaml
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetwork
metadata:
  name: sriov-network-1
  namespace: sriov-network-operator
spec:
  resourceName: intel_sriov_netdevice
  networkNamespace: default
  ipam: |
    {
      "type": "host-local",
      "subnet": "10.56.217.0/24",
      "rangeStart": "10.56.217.171",
      "rangeEnd": "10.56.217.181",
      "routes": [{"dst": "0.0.0.0/0"}],
      "gateway": "10.56.217.1"
    }
```

### Use SR-IOV in pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: sriov-network-1
spec:
  containers:
  - name: test-container
    image: centos:7
    command: ["/bin/sh", "-c", "sleep 99999"]
    resources:
      requests:
        openshift.io/intel_sriov_netdevice: '1'
      limits:
        openshift.io/intel_sriov_netdevice: '1'
```

Verify the SR-IOV interface is attached:

```ShellSession
kubectl exec -it test-pod -- ip link show
# eth0 (primary) + net1 (SR-IOV VF)
```

## DPDK workloads

For DPDK applications, set `deviceType: vfio-pci` in the policy:

```yaml
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetworkNodePolicy
metadata:
  name: policy-dpdk
  namespace: sriov-network-operator
spec:
  nodeSelector:
    feature.node.kubernetes.io/network-sriov.capable: "true"
  resourceName: intel_sriov_dpdk
  numVfs: 4
  nicSelector:
    pfNames: ["ens1f1"]
  deviceType: vfio-pci
```

DPDK pods need hugepages and extra capabilities:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dpdk-pod
spec:
  containers:
  - name: dpdk-app
    image: dpdk-app:latest
    securityContext:
      capabilities:
        add: ["IPC_LOCK", "SYS_RESOURCE"]
    volumeMounts:
    - name: hugepages
      mountPath: /dev/hugepages
    resources:
      requests:
        openshift.io/intel_sriov_dpdk: '2'
        memory: 2Gi
        hugepages-1Gi: 2Gi
      limits:
        openshift.io/intel_sriov_dpdk: '2'
        memory: 2Gi
        hugepages-1Gi: 2Gi
  volumes:
  - name: hugepages
    emptyDir:
      medium: HugePages
```

## Mellanox/NVIDIA NICs

For ConnectX NICs with RDMA:

```yaml
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetworkNodePolicy
metadata:
  name: policy-mellanox
  namespace: sriov-network-operator
spec:
  nodeSelector:
    feature.node.kubernetes.io/network-sriov.capable: "true"
  resourceName: mlnx_sriov_netdevice
  numVfs: 8
  nicSelector:
    vendor: "15b3"
  deviceType: netdevice
  isRdma: true
```

For more details, see the [SR-IOV Network Operator documentation](https://github.com/k8snetworkplumbingwg/sriov-network-operator).
