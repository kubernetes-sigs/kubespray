Weave
=======

Weave 2.0.1 is supported by kubespray

Weave uses [**consensus**](https://www.weave.works/docs/net/latest/ipam/#initialization) mode (default mode) and [**seed**](https://www.weave.works/docs/net/latest/ipam/#initialization) mode.

`Consensus` mode is best to use on static size cluster and `seed` mode is best to use on dynamic size cluster

Weave encryption is supported for all communication

* To use Weave encryption, specify a strong password (if no password, no encrytion)

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_password: EnterPasswordHere
```

This password is used to set an environment variable inside weave container.

Weave is deployed by kubespray using daemonSet

* Check the status of Weave containers

```
# From client
kubectl -n kube-system get pods | grep weave
```

* Check status of weave (connection,encryption ...) for each node

```
# On nodes
curl http://127.0.0.1:6784/status
```

* Check parameters of weave for each node

```
# On nodes
ps -aux | grep weaver
```

### Consensus mode (default mode)

This mode is best to use on static size cluster

### Seed mode

This mode is best to use on dynamic size cluster

The seed mode also allows multi-clouds and hybrid on-premise/cloud clusters deployement.

* Switch from consensus mode to seed mode

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_mode_seed: true
```

These two variables are only used when `weave_mode_seed` is set to `true` (**/!\ do not manually change these values**)

```
# In file ./inventory/group_vars/k8s-cluster.yml
weave_seed: uninitialized
weave_peers: uninitialized
```

The first variable, `weave_seed`, saves the firsts nodes of the weave network

The seconde variable, `weave_peers`, saves IP of all nodes of the weave network

These two variables are used to connect a new node to the weave network. The new node needs to know the firsts nodes (seed) and the list of IPs of all nodes.

To reset these variables and reset the weave network set them to `uninitialized`