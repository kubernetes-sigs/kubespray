# Multus

Multus is a meta CNI plugin that provides multiple network interface support to
pods. For each interface, Multus delegates CNI calls to secondary CNI plugins
such as Calico, macvlan, etc.

See [multus documentation](https://github.com/intel/multus-cni).

## Multus installation

Since Multus itself does not implement networking, it requires a master plugin, which is specified through the variable `kube_network_plugin`. To enable Multus an additional variable `kube_network_plugin_multus` must be set to `true`. For example,

```yml
kube_network_plugin: calico
kube_network_plugin_multus: true
```

will install Multus and Calico and configure Multus to use Calico as the primary network plugin.

## Using Multus

Once Multus is installed, you can create CNI configurations (as a CRD objects) for additional networks, in this case a macvlan CNI configuration is defined. You may replace the config field with any valid CNI configuration where the CNI binary is available on the nodes.

```ShellSession
cat <<EOF | kubectl create -f -
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "macvlan",
      "master": "eth0",
      "mode": "bridge",
      "ipam": {
        "type": "host-local",
        "subnet": "192.168.1.0/24",
        "rangeStart": "192.168.1.200",
        "rangeEnd": "192.168.1.216",
        "routes": [
          { "dst": "0.0.0.0/0" }
        ],
        "gateway": "192.168.1.1"
      }
    }'
EOF
```

You may then create a pod with and additional interface that connects to this network using annotations. The annotation correlates to the name in the NetworkAttachmentDefinition above.

```ShellSession
cat <<EOF | kubectl create -f -
apiVersion: v1
kind: Pod
metadata:
  name: samplepod
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: samplepod
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    image: dougbtv/centos-network
EOF
```

You may now inspect the pod and see that there is an additional interface configured:

```ShellSession
kubectl exec -it samplepod -- ip a
```

For more details on how to use Multus, please visit <https://github.com/intel/multus-cni>
