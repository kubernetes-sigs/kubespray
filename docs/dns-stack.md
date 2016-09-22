K8s DNS stack by Kargo
======================

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

Kargo has yet ways to configure Kubedns addon to forward requests SkyDns can
not answer with authority to arbitrary recursive resolvers. This task is left
for future. See [official SkyDns docs](https://github.com/skynetservices/skydns)
for details.
