# Custom CNI manifest generation

As an example we are using Cilium for testing the network_plugins/custom_cni.

To update the generated manifests to the latest version do the following:

```sh
helm repo add cilium https://helm.cilium.io/
helm repo update
helm template cilium/cilium -n kube-system -f values.yaml > cilium.yaml
```
