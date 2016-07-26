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

K8s components require a loadbalancer to access the apiservers via a reverse
proxy. A kube-proxy does not support multiple apiservers for the time being so
you will need to configure your own loadbalancer to achieve HA. Note that
deploying a loadbalancer is up to a user and is not covered by ansible roles
in Kargo. By default, it only configures a non-HA endpoint, which points to
the `access_ip` or IP address of the first server node in the `kube-master`
group. It can also configure clients to use endpoints for a given loadbalancer
type.

A loadbalancer (LB) may be an external or internal one. An external LB
provides access for external clients, while the internal LB accepts client
connections only to the localhost, similarly to the etcd-proxy HA endpoints.
Given a frontend `VIP` address and `IP1, IP2` addresses of backends, here is
an example configuration for a HAProxy service acting as an external LB:
```
listen kubernetes-apiserver-https
  bind <VIP>:8383
  option ssl-hello-chk
  mode tcp
  timeout client 3h
  timeout server 3h
  server master1 <IP1>:443
  server master2 <IP2>:443
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
is out of scope of this doc.

The internal LB may be the case if you do not want to operate a VIP management
HA stack and require no external and no secure access to the K8s API. The group
var `loadbalancer_apiserver_localhost` (defaults to `false`) controls that
deployment layout. When enabled, it is expected each node in the `k8s-cluster`
group to run a loadbalancer that listens the localhost frontend and has all
of the apiservers as backends. Here is an example configuration for a HAProxy
 service acting as an internal LB:

```
listen kubernetes-apiserver-http
  bind localhost:8080
  mode tcp
  timeout client 3h
  timeout server 3h
  server master1 <IP1>:8080
  server master2 <IP2>:8080
  balance leastconn
```

And the corresponding example global vars config:
```
loadbalancer_apiserver_localhost: true
```

This var overrides an external LB configuration, if any. Note that for this
example, the `kubernetes-apiserver-http` endpoint has backends receiving
unencrypted traffic, which may be a security issue when interconnecting
different nodes, or may be not, if those belong to the isolated management
network without external access.

In order to achieve HA for HAProxy instances, those must be running on the
each node in the `k8s-cluster` group as well, but require no VIP, thus
no VIP management.

Access endpoints are evaluated automagically, as the following:

| Endpoint type                | kube-master   | non-master          |
|------------------------------|---------------|---------------------|
| Local LB (overrides ext)     | http://lc:p   | http://lc:p         |
| External LB, no internal     | https://lb:lp | https://lb:lp       |
| No ext/int LB (default)      | http://lc:p   | https://m[0].aip:sp |

Where:
* `m[0]` - the first node in the `kube-master` group;
* `lb` - LB FQDN, `apiserver_loadbalancer_domain_name`;
* `lc` - localhost;
* `p` - insecure port, `kube_apiserver_insecure_port`
* `sp` - secure port, `kube_apiserver_port`;
* `lp` - LB port, `loadbalancer_apiserver.port`, defers to the secure port;
* `ip` - the node IP, defers to the ansible IP;
* `aip` - `access_ip`, defers to the ip.
