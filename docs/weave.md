Weave
=======

Weave 2.0.1 is supported by kubespray
Weave be use with [**consensus**](https://www.weave.works/docs/net/latest/ipam/#initialization) mode (default mode) and [**seed**](https://www.weave.works/docs/net/latest/ipam/#initialization) mode


In kubespray, Weave encryption for all communication is supported
* For use Weave encryption, it's necessary to specify password
if no password specify, no encrytion
```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_password: EnterPasswordHere
```

Weave is deploy by kubernetes with daemonSet
* Check the status of Weave containers
```
kubectl -n kube-system get pods | grep weave
```
* Check status of weave (connection,encryption ...)
```
curl http://127.0.0.1:6784/status
```

### Consensus mode (default mode)
This mode is to fixed cluster

### Seed mode
This mode is to dynamic cluster
* Change censensus mode to seed mode
```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_mode_seed: true
```
the seed mode allows multi clouds simultaneously and also hybrid on premise/cloud clusters

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_seed: uninitialized
weave_peers: uninitialized
```