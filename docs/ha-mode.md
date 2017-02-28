HA endpoints for K8s
====================

The following components require a highly available endpoints:
* etcd cluster,
* kube-apiserver service instances.

The latter relies on a 3rd side reverse proxies, like Nginx or HAProxy, to
achieve the same goal.

Etcd
----

The `etcd_access_endpoint` fact provides an access pattern for clients. And the
`etcd_multiaccess` (defaults to `True`) group var controlls that behavior.
It makes deployed components to access the etcd cluster members
directly: `http://ip1:2379, http://ip2:2379,...`. This mode assumes the clients
do a loadbalancing and handle HA for connections.


Kube-apiserver
--------------

K8s components require a loadbalancer to access the apiservers via a reverse
proxy. Kargo includes support for an nginx-based proxy that resides on each
non-master Kubernetes node. This is referred to as localhost loadbalancing. It
is less efficient than a dedicated load balancer because it creates extra
health checks on the Kubernetes apiserver, but is more practical for scenarios
where an external LB or virtual IP management is inconvenient.  This option is
configured by the variable `loadbalancer_apiserver_localhost` (defaults to `True`).
You may also define the port the local internal loadbalancer users by changing,
`nginx_kube_apiserver_port`.  This defaults to the value of `kube_apiserver_port`.
It is also import to note that Kargo will only configure kubelet and kube-proxy
on non-master nodes to use the local internal loadbalancer.

If you choose to NOT use the local internal loadbalancer, you will need to configure
your own loadbalancer to achieve HA. Note that deploying a loadbalancer is up to
a user and is not covered by ansible roles in Kargo. By default, it only configures
a non-HA endpoint, which points to the `access_ip` or IP address of the first server
node in the `kube-master` group. It can also configure clients to use endpoints
for a given loadbalancer type. The following diagram shows how traffic to the
apiserver is directed.

![Image](figures/loadbalancer_localhost.png?raw=true)

  Note: Kubernetes master nodes still use insecure localhost access because
  there are bugs in Kubernetes <1.5.0 in using TLS auth on master role
  services. This makes backends receiving unencrypted traffic and may be a
  security issue when interconnecting different nodes, or maybe not, if those
  belong to the isolated management network without external access.

A user may opt to use an external loadbalancer (LB) instead. An external LB
provides access for external clients, while the internal LB accepts client
connections only to the localhost.
Given a frontend `VIP` address and `IP1, IP2` addresses of backends, here is
an example configuration for a HAProxy service acting as an external LB:
```
listen kubernetes-apiserver-https
  bind <VIP>:8383
  option ssl-hello-chk
  mode tcp
  timeout client 3h
  timeout server 3h
  server master1 <IP1>:6443
  server master2 <IP2>:6443
  balance roundrobin
```

And the corresponding example global vars config:
```
apiserver_loadbalancer_domain_name: "lb-apiserver.kubernetes.local"
loadbalancer_apiserver:
  address: <VIP>
  port: 8383
```

This domain name, or default "lb-apiserver.kubernetes.local", will be inserted
into the `/etc/hosts` file of all servers in the `k8s-cluster` group. Note that
the HAProxy service should as well be HA and requires a VIP management, which
is out of scope of this doc. Specifying an external LB overrides any internal
localhost LB configuration.

  Note: In order to achieve HA for HAProxy instances, those must be running on
  the each node in the `k8s-cluster` group as well, but require no VIP, thus
  no VIP management.

Access endpoints are evaluated automagically, as the following:

| Endpoint type                | kube-master   | non-master          |
|------------------------------|---------------|---------------------|
| Local LB (default)           | http://lc:p   | https://lc:nsp      |
| External LB, no internal     | https://lb:lp | https://lb:lp       |
| No ext/int LB                | http://lc:p   | https://m[0].aip:sp |

Where:
* `m[0]` - the first node in the `kube-master` group;
* `lb` - LB FQDN, `apiserver_loadbalancer_domain_name`;
* `lc` - localhost;
* `p` - insecure port, `kube_apiserver_insecure_port`
* `nsp` - nginx secure port, `nginx_kube_apiserver_port`;
* `sp` - secure port, `kube_apiserver_port`;
* `lp` - LB port, `loadbalancer_apiserver.port`, defers to the secure port;
* `ip` - the node IP, defers to the ansible IP;
* `aip` - `access_ip`, defers to the ip.

