Networking plugins
==================

Kargo supports weave, flannel, canal and calico plugins. By default,
the plugins that require a etcd cluster, will share it with kubernetes
components.

Separate etcd cluster for networking plugins
--------------------------------------------

Kargo allows users to define an external etcd cluster endpoint and
certificates/keys location for networking plugins. This isolates plugins' data from
kube components' data that lives in the internal etcd cluster.

There are ``network_plugin_etcd_access_endpoint`` and ``network_plugin_etcd_cert_dir``
vars to define the secure endpoint and certificates/keys location (
defaults to ``/etc/ssl/etcd/ssl/networking_plugins``).

It is expected the following files to be provided by a user in the given certificates
directory of the first internal (for kube components) `etcd` cluster node:

* For calico node/cni `unprivileged` etcd access:
  * ca.pem
  * node.pem
  * node-key.pem
* For `admin` etcd access:
  * ca-key.pem
  * admin.pem
  * admin-key.pem

Note, when configuring the networking plugins with ansible playbooks, that etcd node
distributes these files across all of the k8s-cluster nodes (but the internal etcd
cluster). The files are stored at the same ``network_plugin_etcd_cert_dir`` path.

The first kube-master node must be able to reach the given external etcd endpoint via
HTTPS protocol as well. It is required for the networking plugins configuration stage.
