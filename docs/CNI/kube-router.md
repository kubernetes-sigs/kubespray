# Kube-router

Kube-router is a L3 CNI provider, as such it will setup IPv4 routing between
nodes to provide Pods' networks reachability.

See [kube-router documentation](https://www.kube-router.io/).

## Verifying kube-router install

Kube-router runs its pods as a `DaemonSet` in the `kube-system` namespace:

* Check the status of kube-router pods

```ShellSession
# From the CLI
kubectl get pod --namespace=kube-system -l k8s-app=kube-router -owide

# output
NAME                READY     STATUS    RESTARTS   AGE       IP               NODE                   NOMINATED NODE
kube-router-4f679   1/1       Running   0          2d        192.168.186.4    mykube-k8s-node-nf-2   <none>
kube-router-5slf8   1/1       Running   0          2d        192.168.186.11   mykube-k8s-node-nf-3   <none>
kube-router-lb6k2   1/1       Running   0          20h       192.168.186.14   mykube-k8s-node-nf-6   <none>
kube-router-rzvrb   1/1       Running   0          20h       192.168.186.17   mykube-k8s-node-nf-4   <none>
kube-router-v6n56   1/1       Running   0          2d        192.168.186.6    mykube-k8s-node-nf-1   <none>
kube-router-wwhg8   1/1       Running   0          20h       192.168.186.16   mykube-k8s-node-nf-5   <none>
kube-router-x2xs7   1/1       Running   0          2d        192.168.186.10   mykube-k8s-master-1    <none>
```

* Peek at kube-router container logs:

```ShellSession
# From the CLI
kubectl logs --namespace=kube-system -l k8s-app=kube-router | grep Peer.Up

# output
time="2018-09-17T16:47:14Z" level=info msg="Peer Up" Key=192.168.186.6 State=BGP_FSM_OPENCONFIRM Topic=Peer
time="2018-09-17T16:47:16Z" level=info msg="Peer Up" Key=192.168.186.11 State=BGP_FSM_OPENCONFIRM Topic=Peer
time="2018-09-17T16:47:46Z" level=info msg="Peer Up" Key=192.168.186.10 State=BGP_FSM_OPENCONFIRM Topic=Peer
time="2018-09-18T19:12:24Z" level=info msg="Peer Up" Key=192.168.186.14 State=BGP_FSM_OPENCONFIRM Topic=Peer
time="2018-09-18T19:12:28Z" level=info msg="Peer Up" Key=192.168.186.17 State=BGP_FSM_OPENCONFIRM Topic=Peer
time="2018-09-18T19:12:38Z" level=info msg="Peer Up" Key=192.168.186.16 State=BGP_FSM_OPENCONFIRM Topic=Peer
[...]
```

## Gathering kube-router state

Kube-router Pods come bundled with a "Pod Toolbox" which provides very
useful internal state views for:

* IPVS: via `ipvsadm`
* BGP peering and routing info: via `gobgp`

You need to `kubectl exec -it ...` into a kube-router container to use these, see
<https://www.kube-router.io/docs/pod-toolbox/> for details.

## Kube-router configuration

You can change the default configuration by overriding `kube_router_...` variables
(as found at `roles/network_plugin/kube-router/defaults/main.yml`),
these are named to follow `kube-router` command-line options as per
<https://www.kube-router.io/docs/user-guide/#try-kube-router-with-cluster-installers>.

## Advanced BGP Capabilities

<https://github.com/cloudnativelabs/kube-router#advanced-bgp-capabilities>

If you have other networking devices or SDN systems that talk BGP, kube-router will fit in perfectly.
From a simple full node-to-node mesh to per-node peering configurations, most routing needs can be attained.
The configuration is Kubernetes native (annotations) just like the rest of kube-router.

For more details please refer to the <https://github.com/cloudnativelabs/kube-router/blob/master/docs/bgp.md>.

Next options will set up annotations for kube-router, using `kubectl annotate` command.

```yml
kube_router_annotations_master: []
kube_router_annotations_node: []
kube_router_annotations_all: []
```
