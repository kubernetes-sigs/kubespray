K8s DNS stack by Kargo
======================

For K8s cluster nodes, kargo configures a [Kubernetes DNS](http://kubernetes.io/docs/admin/dns/)
[cluster add-on](http://releases.k8s.io/master/cluster/addons/README.md)
to serve as an authoritative DNS server for a given ``dns_domain`` and its
``svc, default.svc`` default subdomains (a total of ``ndots: 5`` max levels).

Other nodes in the inventory, like external storage nodes or a separate etcd cluster
node group, considered non-cluster and left up to the user to configure DNS resolve.

Note, custom ``ndots`` values affect only the dnsmasq daemon set (explained below).
While the kubedns has the ``ndots=5`` hardcoded, which is not recommended due to
[DNS performance reasons](https://github.com/kubernetes/kubernetes/issues/14051).
You can use config maps for the kubedns app to workaround the issue, which is
yet in the Kargo scope.

Additional search (sub)domains may be defined in the ``searchdomains``
and ``ndots`` vars. And additional recursive DNS resolvers in the `` upstream_dns_servers``,
``nameservers`` vars. Intranet/cloud provider DNS resolvers should be specified
in the first place, followed by external resolvers, for example:

```
skip_dnsmasq: true
nameservers: [8.8.8.8]
upstream_dns_servers: [172.18.32.6]
```
or
```
skip_dnsmasq: false
upstream_dns_servers: [172.18.32.6, 172.18.32.7, 8.8.8.8, 8.8.8.4]
```
The vars are explained below. For the early cluster deployment stage, when there
is yet K8s cluster and apps exist, a user may expect local repos to be
accessible via authoritative intranet resolvers. For that case, if none custom vars
was specified, the default resolver is set to either the cloud provider default
or `8.8.8.8`. And domain is set to the default ``dns_domain`` value as well.
Later, the nameservers will be reconfigured to the DNS service IP that Kargo
configures for K8s cluster.

Also note, existing records will be purged from the `/etc/resolv.conf`,
including resolvconf's base/head/cloud-init config files and those that come from dhclient.
This is required for hostnet pods networking and for [kubelet to not exceed search domains
limits](https://github.com/kubernetes/kubernetes/issues/9229).

Instead, new domain, search, nameserver records and options will be defined from the
aforementioned vars:
* Superseded via dhclient's DNS update hook.
* Generated via cloud-init (CoreOS only).
* Statically defined in the `/etc/resolv.conf`, if none of above is applicable.
* Resolvconf's head/base files are disabled from populating anything into the
  `/etc/resolv.conf`.

It is important to note that multiple search domains combined with high ``ndots``
values lead to poor performance of DNS stack, so please choose it wisely.
The dnsmasq DaemonSet can accept lower ``ndots`` values and return NXDOMAIN
replies for [bogus internal FQDNS](https://github.com/kubernetes/kubernetes/issues/19634#issuecomment-253948954)
before it even hits the kubedns app. This enables dnsmasq to serve as a
protective, but still recursive resolver in front of kubedns.

DNS configuration details
-------------------------

Here is an approximate picture of how DNS things working and
being configured by Kargo ansible playbooks:

![Image](figures/dns.jpeg?raw=true)

Note that an additional dnsmasq daemon set is installed by Kargo
by default. Kubelet will configure DNS base of all pods to use the
given dnsmasq cluster IP, which is defined via the ``dns_server`` var.
The dnsmasq forwards requests for a given cluster ``dns_domain`` to
Kubedns's SkyDns service. The SkyDns server is configured to be an
authoritative DNS server for the given cluser domain (and its subdomains
up to ``ndots:5`` depth). Note: you should scale its replication controller
up, if SkyDns chokes. These two layered DNS forwarders provide HA for the
DNS cluster IP endpoint, which is a critical moving part for Kubernetes apps.

Nameservers are as well configured in the hosts' ``/etc/resolv.conf`` files,
as the given DNS cluster IP merged with ``nameservers`` values. While the
DNS cluster IP merged with the ``upstream_dns_servers`` defines additional
nameservers for the aforementioned nsmasq daemon set running on all hosts.
This mitigates existing Linux limitation of max 3 nameservers in the
``/etc/resolv.conf`` and also brings an additional caching layer for the
clustered DNS services.

You can skip the dnsmasq daemon set install steps by setting the
``skip_dnsmasq: true``. This may be the case, if you're fine with
the nameservers limitation. Sadly, there is no way to work around the
search domain limitations of a 256 chars and 6 domains. Thus, you can
use the ``searchdomains`` var to define no more than a three custom domains.
Remaining three slots are reserved for K8s cluster default subdomains.

When dnsmasq skipped, Kargo redefines the DNS cluster IP to point directly
to SkyDns cluster IP ``skydns_server`` and configures Kubelet's
``--dns_cluster`` to use that IP as well. While this greatly simplifies
things, it comes by the price of limited nameservers though. As you know now,
the DNS cluster IP takes a slot in the ``/etc/resolv.conf``, thus you can
specify no more than a two nameservers for infra and/or external use.
Those may be specified either in ``nameservers`` or ``upstream_dns_servers``
and will be merged together with the ``skydns_server`` IP into the hots'
``/etc/resolv.conf``.

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
