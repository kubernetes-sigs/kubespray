HA endpoints for K8s
====================

The following components require a highly available endpoints:
* etcd cluster,
* kube-apiserver service instances.

The former provides the
[etcd-proxy](https://coreos.com/etcd/docs/latest/proxy.html) service to access
the cluster members in HA fashion.

The latter relies on a 3rd side reverse proxies, like Nginx or HAProxy, to
achieve the same goal.

Etcd
----

Etcd proxies are deployed on each node in the `k8s-cluster` group. A proxy is
a separate etcd process. It has a `localhost:2379` frontend and all of the etcd
cluster members as backends. Note that the `access_ip` is used as the backend
IP, if specified. Frontend endpoints cannot be accessed externally as they are
bound to a localhost only.

The `etcd_access_endpoint` fact provides an access pattern for clients. And the
`etcd_multiaccess` (defaults to `false`) group var controlls that behavior.
When enabled, it makes deployed components to access the etcd cluster members
directly: `http://ip1:2379, http://ip2:2379,...`. This mode assumes the clients
do a loadbalancing and handle HA for connections. Note, a pod definition of a
flannel networking plugin always uses a single `--etcd-server` endpoint!


Kube-apiserver
--------------
TODO(bogdando) TBD
