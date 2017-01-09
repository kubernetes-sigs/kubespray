K8s DNS stack by Kargo
======================

For K8s cluster nodes, kargo configures a [Kubernetes DNS](http://kubernetes.io/docs/admin/dns/)
[cluster add-on](http://releases.k8s.io/master/cluster/addons/README.md)
to serve as an authoritative DNS server for a given ``dns_domain`` and its
``svc, default.svc`` default subdomains (a total of ``ndots: 5`` max levels).

Other nodes in the inventory, like external storage nodes or a separate etcd cluster
node group, considered non-cluster and left up to the user to configure DNS resolve.


DNS variables
=============

There are several global variables which can be used to modify DNS settings:

#### ndots
ndots value to be used in ``/etc/resolv.conf``

It is important to note that multiple search domains combined with high ``ndots``
values lead to poor performance of DNS stack, so please choose it wisely.
The dnsmasq DaemonSet can accept lower ``ndots`` values and return NXDOMAIN
replies for [bogus internal FQDNS](https://github.com/kubernetes/kubernetes/issues/19634#issuecomment-253948954)
before it even hits the kubedns app. This enables dnsmasq to serve as a
protective, but still recursive resolver in front of kubedns.

#### searchdomains
Custom search domains to be added in addition to the cluster search domains (``default.svc.{{ dns_domain }}, svc.{{ dns_domain }}``).

Most Linux systems limit the total number of search domains to 6 and the total length of all search domains
to 256 characters. Depending on the length of ``dns_domain``, you're limitted to less then the total limit.

Please note that ``resolvconf_mode: docker_dns`` will automatically add your systems search domains as
additional search domains. Please take this into the accounts for the limits.

#### nameservers
This variable is only used by ``resolvconf_mode: host_resolvconf``. These nameservers are added to the hosts
``/etc/resolv.conf`` *after* ``upstream_dns_servers`` and thus serve as backup nameservers. If this variable
is not set, a default resolver is chosen (depending on cloud provider or 8.8.8.8 when no cloud provider is specified).

#### upstream_dns_servers
DNS servers to be added *after* the cluster DNS. Used by all ``resolvconf_mode`` modes. These serve as backup
DNS servers in early cluster deployment when no cluster DNS is available yet. These are also added as upstream
DNS servers used by ``dnsmasq`` (when deployed with ``dns_mode: dnsmasq_kubedns``).

DNS modes supported by kargo
============================

You can modify how kargo sets up DNS for your cluster with the variables ``dns_mode`` and ``resolvconf_mode``.

## dns_mode
``dns_mode`` configures how kargo will setup cluster DNS. There are three modes available:

#### dnsmasq_kubedns (default)
This installs an additional dnsmasq DaemonSet which gives more flexibility and lifts some
limitations (e.g. number of nameservers). Kubelet is instructed to use dnsmasq instead of kubedns/skydns.
It is configured to forward all DNS queries belonging to cluster services to kubedns/skydns. All
other queries are forwardet to the nameservers found in ``upstream_dns_servers`` or ``default_resolver``

#### kubedns
This does not install the dnsmasq DaemonSet and instructs kubelet to directly use kubedns/skydns for
all queries.

#### none
This does not install any of dnsmasq and kubedns/skydns. This basically disables cluster DNS completely and
leaves you with a non functional cluster.

## resolvconf_mode
``resolvconf_mode`` configures how kargo will setup DNS for ``hostNetwork: true`` PODs and non-k8s containers.
There are three modes available:

#### docker_dns (default)
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

For normal PODs, k8s will ignore these options and setup its own DNS settings for the PODs, taking
the --cluster_dns (either dnsmasq or kubedns, depending on dns_mode) kubelet option into account.
For ``hostNetwork: true`` PODs however, k8s will let docker setup DNS settings. Docker containers which
are not started/managed by k8s will also use these docker options.

The host system name servers are added to ensure name resolution is also working while cluster DNS is not
running yet. This is especially important in early stages of cluster deployment. In this early stage,
DNS queries to the cluster DNS will timeout after a few seconds, resulting in the system nameserver being
used as a backup nameserver. After cluster DNS is running, all queries will be answered by the cluster DNS
servers, which in turn will forward queries to the system nameserver if required.

#### host_resolvconf
This activates the classic kargo behaviour that modifies the hosts ``/etc/resolv.conf`` file and dhclient
configuration to point to the cluster dns server (either dnsmasq or kubedns, depending on dns_mode).

As cluster DNS is not available on early deployment stage, this mode is split into 2 stages. In the first
stage (``dns_early: true``), ``/etc/resolv.conf`` is configured to use the DNS servers found in ``upstream_dns_servers``
and ``nameservers``. Later, ``/etc/resolv.conf`` is reconfigured to use the cluster DNS server first, leaving
the other nameservers as backups.

Also note, existing records will be purged from the `/etc/resolv.conf`,
including resolvconf's base/head/cloud-init config files and those that come from dhclient.

#### none
Does nothing regarding ``/etc/resolv.conf``. This leaves you with a cluster that works as expected in most cases.
The only exception is that ``hostNetwork: true`` PODs and non-k8s managed containers will not be able to resolve
cluster service names.


Limitations
-----------

* Kargo has yet ways to configure Kubedns addon to forward requests SkyDns can
  not answer with authority to arbitrary recursive resolvers. This task is left
  for future. See [official SkyDns docs](https://github.com/skynetservices/skydns)
  for details.

* There is
  [no way to specify a custom value](https://github.com/kubernetes/kubernetes/issues/33554)
  for the SkyDNS ``ndots`` param via an
  [option for KubeDNS](https://github.com/kubernetes/kubernetes/blob/master/cmd/kube-dns/app/options/options.go)
  add-on, while SkyDNS supports it though.

* the ``searchdomains`` have a limitation of a 6 names and 256 chars
  length. Due to default ``svc, default.svc`` subdomains, the actual
  limits are a 4 names and 239 chars respectively.

* the ``nameservers`` have a limitation of a 3 servers, although there
  is a way to mitigate that with the ``upstream_dns_servers``,
  see below. Anyway, the ``nameservers`` can take no more than a two
  custom DNS servers because of one slot is reserved for a Kubernetes
  cluster needs.
