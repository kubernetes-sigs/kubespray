# K8s DNS stack by Kubespray

For K8s cluster nodes, Kubespray configures a [Kubernetes DNS](https://kubernetes.io/docs/admin/dns/)
[cluster add-on](https://releases.k8s.io/master/cluster/addons/README.md)
to serve as an authoritative DNS server for a given ``dns_domain`` and its
``svc, default.svc`` default subdomains (a total of ``ndots: 5`` max levels).

Other nodes in the inventory, like external storage nodes or a separate etcd cluster
node group, considered non-cluster and left up to the user to configure DNS resolve.

## DNS variables

There are several global variables which can be used to modify DNS settings:

### ndots

ndots value to be used in ``/etc/resolv.conf``

It is important to note that multiple search domains combined with high ``ndots``
values lead to poor performance of DNS stack, so please choose it wisely.

## dns_timeout

timeout value to be used in ``/etc/resolv.conf``

## dns_attempts

attempts value to be used in ``/etc/resolv.conf``

### searchdomains

Custom search domains to be added in addition to the cluster search domains (``default.svc.{{ dns_domain }}, svc.{{ dns_domain }}``).

Most Linux systems limit the total number of search domains to 6 and the total length of all search domains
to 256 characters. Depending on the length of ``dns_domain``, you're limited to less than the total limit.

`remove_default_searchdomains: true` will remove the default cluster search domains.

Please note that ``resolvconf_mode: docker_dns`` will automatically add your systems search domains as
additional search domains. Please take this into the accounts for the limits.

### nameservers

This variable is only used by ``resolvconf_mode: host_resolvconf``. These nameservers are added to the hosts
``/etc/resolv.conf`` *after* ``upstream_dns_servers`` and thus serve as backup nameservers. If this variable
is not set, a default resolver is chosen (depending on cloud provider or 8.8.8.8 when no cloud provider is specified).

### upstream_dns_servers

DNS servers to be added *after* the cluster DNS. Used by all ``resolvconf_mode`` modes. These serve as backup
DNS servers in early cluster deployment when no cluster DNS is available yet.

### dns_upstream_forward_extra_opts

Whether or not upstream DNS servers come from `upstream_dns_servers` variable or /etc/resolv.conf, related forward block in coredns (and nodelocaldns) configuration can take options (see <https://coredns.io/plugins/forward/> for details).
These are configurable in inventory in as a dictionary in the `dns_upstream_forward_extra_opts` variable.
By default, no other option than the ones hardcoded (see `roles/kubernetes-apps/ansible/templates/coredns-config.yml.j2` and `roles/kubernetes-apps/ansible/templates/nodelocaldns-config.yml.j2`).

### coredns_kubernetes_extra_opts

Custom options to be added to the kubernetes coredns plugin.

### coredns_kubernetes_extra_domains

Extra domains to be forwarded to the kubernetes coredns plugin.

### coredns_rewrite_block

[Rewrite](https://coredns.io/plugins/rewrite/) plugin block to perform internal message rewriting.

### coredns_external_zones

Array of optional external zones to coredns forward queries to. It's  injected into
`coredns`' config file before default kubernetes zone. Use it as an optimization for well-known zones and/or internal-only
domains, i.e. VPN for internal networks (default is unset)

Example:

```yaml
coredns_external_zones:
- zones:
  - example.com
  - example.io:1053
  nameservers:
  - 1.1.1.1
  - 2.2.2.2
  cache: 5
- zones:
  - https://mycompany.local:4453
  nameservers:
  - 192.168.0.53
  cache: 0
- zones:
  - mydomain.tld
  nameservers:
  - 10.233.0.3
  cache: 5
  rewrite:
  - name stop website.tld website.namespace.svc.cluster.local
```

or as INI

```ini
coredns_external_zones='[{"cache": 30,"zones":["example.com","example.io:453"],"nameservers":["1.1.1.1","2.2.2.2"]}]'
```

### dns_etchosts (coredns)

Optional hosts file content to coredns use as /etc/hosts file. This will also be used by nodelocaldns, if enabled.

Example:

```yaml
dns_etchosts: |
  192.168.0.100 api.example.com
  192.168.0.200 ingress.example.com
```

### enable_coredns_reverse_dns_lookups

Whether reverse DNS lookups are enabled in the coredns config. Defaults to `true`.

### CoreDNS default zone cache plugin

If you wish to configure the caching behaviour of CoreDNS on the default zone, you can do so using the `coredns_default_zone_cache_block` string block.

An example value (more information on the [plugin's documentation](https://coredns.io/plugins/cache/)) to:

* raise the max cache TTL to 3600 seconds
* raise the max amount of success responses to cache to 3000
* disable caching of denial responses altogether
* enable pre-fetching of lookups with at least 10 lookups per minute before they expire

Would be as follows:

```yaml
coredns_default_zone_cache_block: |
  cache 3600 {
    success 3000
    denial 0
    prefetch 10 1m
  }
```

## DNS modes supported by Kubespray

You can modify how Kubespray sets up DNS for your cluster with the variables ``dns_mode`` and ``resolvconf_mode``.

### dns_mode

``dns_mode`` configures how Kubespray will setup cluster DNS. There are four modes available:

#### dns_mode: coredns (default)

This installs CoreDNS as the default cluster DNS for all queries.

#### dns_mode: coredns_dual

This installs CoreDNS as the default cluster DNS for all queries, plus a secondary CoreDNS stack.

#### dns_mode: manual

This does not install coredns, but allows you to specify
`manual_dns_server`, which will be configured on nodes for handling Pod DNS.
Use this method if you plan to install your own DNS server in the cluster after
initial deployment.

#### dns_mode: none

This does not install any of DNS solution at all. This basically disables cluster DNS completely and
leaves you with a non functional cluster.

## resolvconf_mode

``resolvconf_mode`` configures how Kubespray will setup DNS for ``hostNetwork: true`` PODs and non-k8s containers.
There are three modes available:

### resolvconf_mode: host_resolvconf (default)

This activates the classic Kubespray behavior that modifies the hosts ``/etc/resolv.conf`` file and dhclient
configuration to point to the cluster dns server (either coredns or coredns_dual, depending on dns_mode).

As cluster DNS is not available on early deployment stage, this mode is split into 2 stages. In the first
stage (``dns_early: true``), ``/etc/resolv.conf`` is configured to use the DNS servers found in ``upstream_dns_servers``
and ``nameservers``. Later, ``/etc/resolv.conf`` is reconfigured to use the cluster DNS server first, leaving
the other nameservers as backups.

Also note, existing records will be purged from the `/etc/resolv.conf`,
including resolvconf's base/head/cloud-init config files and those that come from dhclient.

### resolvconf_mode: docker_dns

This sets up the docker daemon with additional --dns/--dns-search/--dns-opt flags.

The following nameservers are added to the docker daemon (in the same order as listed here):

* cluster nameserver (depends on dns_mode)
* content of optional upstream_dns_servers variable
* host system nameservers (read from hosts /etc/resolv.conf)

The following search domains are added to the docker daemon (in the same order as listed here):

* cluster domains (``default.svc.{{ dns_domain }}``, ``svc.{{ dns_domain }}``)
* content of optional searchdomains variable
* host system search domains (read from hosts /etc/resolv.conf)

The following dns options are added to the docker daemon

* ndots:{{ ndots }}
* timeout:2
* attempts:2

These dns options can be overridden by setting a different list:

```yaml
docker_dns_options:
- ndots:{{ ndots }}
- timeout:2
- attempts:2
- rotate
```

For normal PODs, k8s will ignore these options and setup its own DNS settings for the PODs, taking
the --cluster_dns (either coredns or coredns_dual, depending on dns_mode) kubelet option into account.
For ``hostNetwork: true`` PODs however, k8s will let docker setup DNS settings. Docker containers which
are not started/managed by k8s will also use these docker options.

The host system name servers are added to ensure name resolution is also working while cluster DNS is not
running yet. This is especially important in early stages of cluster deployment. In this early stage,
DNS queries to the cluster DNS will timeout after a few seconds, resulting in the system nameserver being
used as a backup nameserver. After cluster DNS is running, all queries will be answered by the cluster DNS
servers, which in turn will forward queries to the system nameserver if required.

### resolvconf_mode: none

Does nothing regarding ``/etc/resolv.conf``. This leaves you with a cluster that works as expected in most cases.
The only exception is that ``hostNetwork: true`` PODs and non-k8s managed containers will not be able to resolve
cluster service names.

## Nodelocal DNS cache

Setting ``enable_nodelocaldns`` to ``true`` will make pods reach out to the dns (core-dns) caching agent running on the same node, thereby avoiding iptables DNAT rules and connection tracking. The local caching agent will query core-dns (depending on what main DNS plugin is configured in your cluster) for cache misses of cluster hostnames(cluster.local suffix by default).

More information on the rationale behind this implementation can be found [here](https://github.com/kubernetes/enhancements/blob/master/keps/sig-network/1024-nodelocal-cache-dns/README.md).

**As per the 2.10 release, Nodelocal DNS cache is enabled by default.**

### External zones

It's possible to extent the `nodelocaldns`' configuration by adding an array of external zones. For example:

```yaml
nodelocaldns_external_zones:
- zones:
  - example.com
  - example.io:1053
  nameservers:
  - 1.1.1.1
  - 2.2.2.2
  cache: 5
- zones:
  - https://mycompany.local:4453
  nameservers:
  - 192.168.0.53
```

### dns_etchosts (nodelocaldns)

See [dns_etchosts](#dns_etchosts-coredns) above.

### Nodelocal DNS HA

Under some circumstances the single POD nodelocaldns implementation may not be able to be replaced soon enough and a cluster upgrade or a nodelocaldns upgrade can cause DNS requests to time out for short intervals. If for any reason your applications cannot tolerate this behavior you can enable a redundant nodelocal DNS pod on each node:

```yaml
enable_nodelocaldns_secondary: true
```

**Note:** when the nodelocaldns secondary is enabled, the primary is instructed to no longer tear down the iptables rules it sets up to direct traffic to itself. In case both daemonsets have failing pods on the same node, this can cause a DNS blackout with traffic no longer being forwarded to the coredns central service as a fallback. Please ensure you account for this also if you decide to disable the nodelocaldns cache.

There is a time delta (in seconds) allowed for the secondary nodelocaldns to survive in case both primary and secondary daemonsets are updated at the same time. It is advised to tune this variable after you have performed some tests in your own environment.

```yaml
nodelocaldns_secondary_skew_seconds: 5
```

## Limitations

* Kubespray has yet ways to configure Kubedns addon to forward requests SkyDns can
  not answer with authority to arbitrary recursive resolvers. This task is left
  for future. See [official SkyDns docs](https://github.com/skynetservices/skydns)
  for details.

* There is
  [no way to specify a custom value](https://github.com/kubernetes/kubernetes/issues/33554)
  for the SkyDNS ``ndots`` param.

* the ``searchdomains`` have a limitation of a 6 names and 256 chars
  length. Due to default ``svc, default.svc`` subdomains, the actual
  limits are a 4 names and 239 chars respectively. If `remove_default_searchdomains: true`
  added you are back to 6 names.

* the ``nameservers`` have a limitation of a 3 servers, although there
  is a way to mitigate that with the ``upstream_dns_servers``,
  see below. Anyway, the ``nameservers`` can take no more than a two
  custom DNS servers because of one slot is reserved for a Kubernetes
  cluster needs.
