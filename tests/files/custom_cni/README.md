# Custom CNI manifest generation

As an example we are using Cilium for testing the network_plugins/custom_cni.

To update the generated manifests to the latest version do the following:

```sh
helm repo add cilium https://helm.cilium.io/
helm repo update
helm template cilium/cilium -n kube-system -f values.yaml > cilium.yaml
```

The generated Cilium manifest contains resources in both the `kube-system` and
`cilium-secrets` namespaces. Configure the static manifest example without a
kubectl namespace argument:

```yaml
custom_cni_manifests:
  - "{{ playbook_dir }}/../tests/files/custom_cni/cilium.yaml"
custom_cni_namespace: ""
```

When `custom_cni_namespace` is empty, every namespaced resource in the
manifests should declare `metadata.namespace`. Otherwise, kubectl applies the
resource to the current context's default namespace.
