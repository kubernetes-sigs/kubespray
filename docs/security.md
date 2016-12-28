Users and groups
================

There are following users and groups defined by the addusers role:

* Kube user, group from the ``kubelet_user`` and ``kubelet_group`` vars.
* Etcd user, group from the ``etcd_user`` and ``etcd_group`` vars.
* Network plugin user, group from the ``netplug_user`` and ``netplug_group`` vars.

There are additional certificate access groups for kube and etcd users defined.
For example, kubelet and network plugins require read access to the
etcd certs and keys. This is defined via the corresponding ``etcd_cert_group``
var. Members of that group (defaults to `kube` and `netplug` users) will read
etcd secret keys and certs. Same applies to the ``kube_cert_group``
(defaults to `kube` user) members. You may want to share kube certs via that
group with bastion proxies or the like.

Linux capabilites
=================

Kargo allows to control dropped Linux capabilities for unprivileged docker
containers it configures for deployments. For examle, etcd or some networking
related systemd units or k8s workloads, like kubedns, dnsmasq or netchecker apps.

Dropped capabilites are represented by the ``apps_drop_cap``, ``dnsmasq_drop_cap``,
``etcd_drop_cap``, ``calico_drop_cap``  vars.

Be carefull changing defaults - different kube components and k8s apps might
expect specific capabilities to be present and can only run as root! Also note
that kublet, kube-proxy and network plugins require privileged mode and ignore
dropped capabilities.
