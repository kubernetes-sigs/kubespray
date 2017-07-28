Weave
=======

Weave 2.0.1 is supported by kubespray

Weave be use with [**consensus**](https://www.weave.works/docs/net/latest/ipam/#initialization) mode (default mode) and [**seed**](https://www.weave.works/docs/net/latest/ipam/#initialization) mode

In kubespray, Weave encryption for all communication is supported

* For use Weave encryption, it's necessary to specify password (if no password specify, no encrytion)

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_password: EnterPasswordHere
```

This password is use in environment variable in weave container. So it's impossible to see it somewhere

Weave is deploy by kubernetes with daemonSet

* Check the status of Weave containers

```
# On k8s master
kubectl -n kube-system get pods | grep weave
```

* Check status of weave (connection,encryption ...)

```
# On node
curl http://127.0.0.1:6784/status
```

* Check parameters of weave

```
# On node
ps -aux | grep weaver
```

### Consensus mode (default mode)

This mode is to fixed cluster

### Seed mode

This mode is to dynamic cluster

the seed mode allows multi clouds simultaneously and also hybrid on premise/cloud clusters

* Change consensus mode to seed mode

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_mode_seed: true
```

This two variables are use to have automaticaly dynamic cluster (**/!\ do not manually change these values**)

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_seed: uninitialized
weave_peers: uninitialized
```

The first variable, `weave_seed`, allows to save the first or firsts nodes of the weave network

The seconde variable, `weave_peers`, allows to save IP of all nodes of the weave network

these two variables allows to connecte a new node to the weave network. this new node need to know the first node (seed) and list of IP to all node of network

For reset these variables set there values to `uninitialized`