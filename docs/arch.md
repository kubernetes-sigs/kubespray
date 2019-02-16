## Architecture compatibility

The following table shows the impact of the CPU architecture on compatible features:
- amd64: Cluster using only x86/amd64 CPUs
- arm64: Cluster using only arm64 CPUs
- amd64 + arm64: Cluster with a mix of x86/amd64 and arm64 CPUs

| kube_network_plugin | amd64 | arm64 | amd64 + arm64 |
| ------------------- | ----- | ----- | ------------- |
| Calico              | Y     | Y     | Y             |
| Weave               | Y     | Y     | Y             |
| Flannel             | Y     | N     | N             |
| Canal               | Y     | N     | N             |
| Cilium              | Y     | N     | N             |
| Contib              | Y     | N     | N             |
| kube-router         | Y     | N     | N             |
