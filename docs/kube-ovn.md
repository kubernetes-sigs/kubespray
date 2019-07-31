Kube-OVN
===========
Kube-OVN integrates the OVN-based Network Virtualization with Kubernetes. It offers an advanced Container Network Fabric for Enterprises.

For more information please check [Kube-OVN documentation](https://github.com/alauda/kube-ovn)

## How to use it

Enable kube-ovn in `group_vars/k8s-cluster/k8s-cluster.yml`
```
...
kube_network_plugin: kube-ovn
...
```

## Verifying kube-ovn install

Kube-OVN run ovn and controller in `kube-ovn` namespace

* Check the status of kube-ovn pods

```
# From the CLI
kubectl get pod -n kube-ovn

# Output
NAME                                   READY   STATUS    RESTARTS   AGE
kube-ovn-cni-49lsm                     1/1     Running   0          2d20h
kube-ovn-cni-9db8f                     1/1     Running   0          2d20h
kube-ovn-cni-wftdk                     1/1     Running   0          2d20h
kube-ovn-controller-68d7bb48bd-7tnvg   1/1     Running   0          2d21h
ovn-central-6675dbb7d9-d7z8m           1/1     Running   0          4d16h
ovs-ovn-hqn8p                          1/1     Running   0          4d16h
ovs-ovn-hvpl8                          1/1     Running   0          4d16h
ovs-ovn-r5frh                          1/1     Running   0          4d16h
```

* Check the default and node subnet

```
# From the CLI
kubectl get subnet

# Output
NAME          PROTOCOL   CIDR            PRIVATE   NAT
join          IPv4       100.64.0.0/16   false     false
ovn-default   IPv4       10.16.0.0/16    false     true
```