K8s DNS stack by Kargo
======================

Here is an approximate picture of how DNS things working and
being configured by Kargo ansible playbooks:

![Image](figures/dns.png?raw=true)

Note that an additional dnsmasq daemon set is installed by Kargo
by default. Kubelet will configure DNS base of all pods to use that
dnsmasq cluster IP. You can disable it with the ``skip_dnsmasq``
var. This may be the case, if you're fine with Linux limit of max 3
nameservers in the ``/etc/resolv.conf``. When skipped and bypassed
directly to Kubedns's dnsmasq cluster IP, it greatly simplifies things
by the price of limited nameservers though.

Nameservers are configured in the hosts' ``/etc/resolv.conf`` files
from the ``nameservers`` (see also ``searchdomains``) vars. While the
``upstream_dns_servers`` will define additional DNS servers for the
dnsmasq daemon set running on all hosts (unless bypassed with
``skip_dnsmasq``).
