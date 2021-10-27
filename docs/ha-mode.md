# HA endpoints for K8s

The following components require a highly available endpoints:

* etcd cluster,
* kube-apiserver service instances.

The latter relies on a 3rd side reverse proxy, like Nginx or HAProxy, to
achieve the same goal.

## Etcd

The etcd clients (kube-api-masters) are configured with the list of all etcd peers. If the etcd-cluster has multiple instances, it's configured in HA already.

## Kube-apiserver

K8s components require a loadbalancer to access the apiservers via a reverse
proxy. Kubespray includes support for an nginx-based proxy that resides on each
non-master Kubernetes node. This is referred to as localhost loadbalancing. It
is less efficient than a dedicated load balancer because it creates extra
health checks on the Kubernetes apiserver, but is more practical for scenarios
where an external LB or virtual IP management is inconvenient.  This option is
configured by the variable `loadbalancer_apiserver_localhost` (defaults to
`True`. Or `False`, if there is an external `loadbalancer_apiserver` defined).
You may also define the port the local internal loadbalancer uses by changing,
`loadbalancer_apiserver_port`.  This defaults to the value of
`kube_apiserver_port`. It is also important to note that Kubespray will only
configure kubelet and kube-proxy on non-master nodes to use the local internal
loadbalancer.

If you choose to NOT use the local internal loadbalancer, you will need to
configure your own loadbalancer to achieve HA. Note that deploying a
loadbalancer is up to a user and is not covered by ansible roles in Kubespray.
By default, it only configures a non-HA endpoint, which points to the
`access_ip` or IP address of the first server node in the `kube_control_plane` group.
It can also configure clients to use endpoints for a given loadbalancer type.
The following diagram shows how traffic to the apiserver is directed.

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

```raw
listen kubernetes-apiserver-https
  bind <VIP>:8383
  mode tcp
  option log-health-checks
  timeout client 3h
  timeout server 3h
  server master1 <IP1>:6443 check check-ssl verify none inter 10000
  server master2 <IP2>:6443 check check-ssl verify none inter 10000
  balance roundrobin
```

  Note: That's an example config managed elsewhere outside of Kubespray.

And the corresponding example global vars for such a "cluster-aware"
external LB with the cluster API access modes configured in Kubespray:

```yml
apiserver_loadbalancer_domain_name: "my-apiserver-lb.example.com"
loadbalancer_apiserver:
  address: <VIP>
  port: 8383
```

  Note: The default kubernetes apiserver configuration binds to all interfaces,
  so you will need to use a different port for the vip from that the API is
  listening on, or set the `kube_apiserver_bind_address` so that the API only
  listens on a specific interface (to avoid conflict with haproxy binding the
  port on the VIP address)

This domain name, or default "lb-apiserver.kubernetes.local", will be inserted
into the `/etc/hosts` file of all servers in the `k8s_cluster` group and wired
into the generated self-signed TLS/SSL certificates as well. Note that
the HAProxy service should as well be HA and requires a VIP management, which
is out of scope of this doc.

There is a special case for an internal and an externally configured (not with
Kubespray) LB used simultaneously. Keep in mind that the cluster is not aware
of such an external LB and you need no to specify any configuration variables
for it.

  Note: TLS/SSL termination for externally accessed API endpoints' will **not**
  be covered by Kubespray for that case. Make sure your external LB provides it.
  Alternatively you may specify an externally load balanced VIPs in the
  `supplementary_addresses_in_ssl_keys` list. Then, kubespray will add them into
  the generated cluster certificates as well.

Aside of that specific case, the `loadbalancer_apiserver` considered mutually
exclusive to `loadbalancer_apiserver_localhost`.

Access API endpoints are evaluated automatically, as the following:

| Endpoint type                | kube_control_plane | non-master              | external              |
|------------------------------|--------------------|-------------------------|-----------------------|
| Local LB (default)           | `https://bip:sp`   | `https://lc:nsp`        | `https://m[0].aip:sp` |
| Local LB + Unmanaged here LB | `https://bip:sp`   | `https://lc:nsp`        | `https://ext`         |
| External LB, no internal     | `https://bip:sp`   | `<https://lb:lp>`       | `https://lb:lp`       |
| No ext/int LB                | `https://bip:sp`   | `<https://m[0].aip:sp>` | `https://m[0].aip:sp` |

Where:

* `m[0]` - the first node in the `kube_control_plane` group;
* `lb` - LB FQDN, `apiserver_loadbalancer_domain_name`;
* `ext` - Externally load balanced VIP:port and FQDN, not managed by Kubespray;
* `lc` - localhost;
* `bip` - a custom bind IP or localhost for the default bind IP '0.0.0.0';
* `nsp` - nginx secure port, `loadbalancer_apiserver_port`, defers to `sp`;
* `sp` - secure port, `kube_apiserver_port`;
* `lp` - LB port, `loadbalancer_apiserver.port`, defers to the secure port;
* `ip` - the node IP, defers to the ansible IP;
* `aip` - `access_ip`, defers to the ip.

A second and a third column represent internal cluster access modes. The last
column illustrates an example URI to access the cluster APIs externally.
Kubespray has nothing to do with it, this is informational only.

As you can see, the masters' internal API endpoints are always
contacted via the local bind IP, which is `https://bip:sp`.

**Note** that for some cases, like healthchecks of applications deployed by
Kubespray, the masters' APIs are accessed via the insecure endpoint, which
consists of the local `kube_apiserver_insecure_bind_address` and
`kube_apiserver_insecure_port`.

## Optional configurations

### ETCD with a LB

In order to use an external loadbalancing (L4/TCP or L7 w/ SSL Passthrough VIP), the following variables need to be overridden in group_vars

* `etcd_access_addresses`
* `etcd_client_url`
* `etcd_cert_alt_names`
* `etcd_cert_alt_ips`

#### Example of a VIP w/ FQDN

```yaml
etcd_access_addresses: https://etcd.example.com:2379
etcd_client_url: https://etcd.example.com:2379
etcd_cert_alt_names:
  - "etcd.kube-system.svc.{{ dns_domain }}"
  - "etcd.kube-system.svc"
  - "etcd.kube-system"
  - "etcd"
  - "etcd.example.com" # This one needs to be added to the default etcd_cert_alt_names
```

#### Example of a VIP w/o FQDN (IP only)

```yaml
etcd_access_addresses: https://2.3.7.9:2379
etcd_client_url: https://2.3.7.9:2379
etcd_cert_alt_ips:
  - "2.3.7.9"
```
