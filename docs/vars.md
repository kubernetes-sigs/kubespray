# Configurable Parameters in Kubespray

## Generic Ansible variables

You can view facts gathered by Ansible automatically
[here](https://docs.ansible.com/ansible/latest/playbooks_variables.html#information-discovered-from-systems-facts).

Some variables of note include:

* *ansible_user*: user to connect to via SSH
* *ansible_default_ipv4.address*: IP address Ansible automatically chooses.
  Generated based on the output from the command ``ip -4 route get 8.8.8.8``

## Common vars that are used in Kubespray

* *calico_version* - Specify version of Calico to use
* *calico_cni_version* - Specify version of Calico CNI plugin to use
* *docker_version* - Specify version of Docker to used (should be quoted
  string). Must match one of the keys defined for *docker_versioned_pkg*
  in `roles/container-engine/docker/vars/*.yml`.
* *containerd_version* - Specify version of Containerd to use
* *etcd_version* - Specify version of ETCD to use
* *ipip* - Enables Calico ipip encapsulation by default
* *kube_network_plugin* - Sets k8s network plugin (default Calico)
* *kube_proxy_mode* - Changes k8s proxy mode to iptables mode
* *kube_version* - Specify a given Kubernetes version
* *searchdomains* - Array of DNS domains to search when looking up hostnames
* *nameservers* - Array of nameservers to use for DNS lookup
* *preinstall_selinux_state* - Set selinux state, permitted values are permissive and disabled.

## Addressing variables

* *ip* - IP to use for binding services (host var)
* *access_ip* - IP for other hosts to use to connect to. Often required when
  deploying from a cloud, such as OpenStack or GCE and you have separate
  public/floating and private IPs.
* *ansible_default_ipv4.address* - Not Kubespray-specific, but it is used if ip
  and access_ip are undefined
* *loadbalancer_apiserver* - If defined, all hosts will connect to this
  address instead of localhost for kube_control_planes and kube_control_plane[0] for
  kube_nodes. See more details in the
  [HA guide](/docs/ha-mode.md).
* *loadbalancer_apiserver_localhost* - makes all hosts to connect to
  the apiserver internally load balanced endpoint. Mutual exclusive to the
  `loadbalancer_apiserver`. See more details in the
  [HA guide](/docs/ha-mode.md).

## Cluster variables

Kubernetes needs some parameters in order to get deployed. These are the
following default cluster parameters:

* *cluster_name* - Name of cluster (default is cluster.local)
* *container_manager* - Container Runtime to install in the nodes (default is docker)
* *dns_domain* - Name of cluster DNS domain (default is cluster.local)
* *kube_network_plugin* - Plugin to use for container networking
* *kube_service_addresses* - Subnet for cluster IPs (default is
  10.233.0.0/18). Must not overlap with kube_pods_subnet
* *kube_pods_subnet* - Subnet for Pod IPs (default is 10.233.64.0/18). Must not
  overlap with kube_service_addresses.
* *kube_network_node_prefix* - Subnet allocated per-node for pod IPs. Remaining
  bits in kube_pods_subnet dictates how many kube_nodes can be in cluster. Setting this > 25 will
  raise an assertion in playbooks if the `kubelet_max_pods` var also isn't adjusted accordingly
  (assertion not applicable to calico which doesn't use this as a hard limit, see
  [Calico IP block sizes](https://docs.projectcalico.org/reference/resources/ippool#block-sizes).
* *enable_dual_stack_networks* - Setting this to true will provision both IPv4 and IPv6 networking for pods and services.
* *kube_service_addresses_ipv6* - Subnet for cluster IPv6 IPs (default is ``fd85:ee78:d8a6:8607::1000/116``). Must not overlap with ``kube_pods_subnet_ipv6``.
* *kube_pods_subnet_ipv6* - Subnet for Pod IPv6 IPs (default is ``fd85:ee78:d8a6:8607::1:0000/112``). Must not overlap with ``kube_service_addresses_ipv6``.
* *kube_network_node_prefix_ipv6* - Subnet allocated per-node for pod IPv6 IPs. Remaining bits in ``kube_pods_subnet_ipv6`` dictates how many kube_nodes can be in cluster.
* *skydns_server* - Cluster IP for DNS (default is 10.233.0.3)
* *skydns_server_secondary* - Secondary Cluster IP for CoreDNS used with coredns_dual deployment (default is 10.233.0.4)
* *enable_coredns_k8s_external* - If enabled, it configures the [k8s_external plugin](https://coredns.io/plugins/k8s_external/)
  on the CoreDNS service.
* *coredns_k8s_external_zone* - Zone that will be used when CoreDNS k8s_external plugin is enabled
  (default is k8s_external.local)
* *enable_coredns_k8s_endpoint_pod_names* - If enabled, it configures endpoint_pod_names option for kubernetes plugin.
  on the CoreDNS service.
* *cloud_provider* - Enable extra Kubelet option if operating inside GCE or
  OpenStack (default is unset)
* *kube_feature_gates* - A list of key=value pairs that describe feature gates for
  alpha/experimental Kubernetes features. (defaults is `[]`)
* *kubeadm_feature_gates* - A list of key=value pairs that describe feature gates for
  alpha/experimental Kubeadm features. (defaults is `[]`)
* *authorization_modes* - A list of [authorization mode](
https://kubernetes.io/docs/admin/authorization/#using-flags-for-your-authorization-module)
  that the cluster should be configured for. Defaults to `['Node', 'RBAC']`
  (Node and RBAC authorizers).
  Note: `Node` and `RBAC` are enabled by default. Previously deployed clusters can be
  converted to RBAC mode. However, your apps which rely on Kubernetes API will
  require a service account and cluster role bindings. You can override this
  setting by setting authorization_modes to `[]`.

Note, if cloud providers have any use of the ``10.233.0.0/16``, like instances'
private addresses, make sure to pick another values for ``kube_service_addresses``
and ``kube_pods_subnet``, for example from the ``172.18.0.0/16``.

## Enabling Dual Stack (IPV4 + IPV6) networking

If *enable_dual_stack_networks* is set to ``true``, Dual Stack networking will be enabled in the cluster. This will use the default IPv4 and IPv6 subnets specified in the defaults file in the ``kubespray-defaults`` role, unless overridden of course. The default config will give you room for up to 256 nodes with 126 pods per node, and up to 4096 services.

## DNS variables

By default, hosts are set up with 8.8.8.8 as an upstream DNS server and all
other settings from your existing /etc/resolv.conf are lost. Set the following
variables to match your requirements.

* *upstream_dns_servers* - Array of upstream DNS servers configured on host in
  addition to Kubespray deployed DNS
* *nameservers* - Array of DNS servers configured for use by hosts
* *searchdomains* - Array of up to 4 search domains
* *dns_etchosts* - Content of hosts file for coredns and nodelocaldns

For more information, see [DNS
Stack](https://github.com/kubernetes-sigs/kubespray/blob/master/docs/dns-stack.md).

## Other service variables

* *docker_options* - Commonly used to set
  ``--insecure-registry=myregistry.mydomain:5000``
* *docker_plugins* - This list can be used to define [Docker plugins](https://docs.docker.com/engine/extend/) to install.
* *containerd_default_runtime* - Sets the default Containerd runtime used by the Kubernetes CRI plugin.
* *containerd_runtimes* - Sets the Containerd runtime attributes used by the Kubernetes CRI plugin.
  [Default config](https://github.com/kubernetes-sigs/kubespray/blob/master/roles/container-engine/containerd/defaults/main.yml) can be overriden in inventory vars.
* *http_proxy/https_proxy/no_proxy/no_proxy_exclude_workers/additional_no_proxy* - Proxy variables for deploying behind a
  proxy. Note that no_proxy defaults to all internal cluster IPs and hostnames
  that correspond to each node.
* *kubelet_cgroup_driver* - Allows manual override of the
  cgroup-driver option for Kubelet. By default autodetection is used
  to match Docker configuration.
* *kubelet_rotate_certificates* - Auto rotate the kubelet client certificates by requesting new certificates
  from the kube-apiserver when the certificate expiration approaches.
* *kubelet_rotate_server_certificates* - Auto rotate the kubelet server certificates by requesting new certificates
  from the kube-apiserver when the certificate expiration approaches.
  **Note** that server certificates are **not** approved automatically. Approve them manually
  (`kubectl get csr`, `kubectl certificate approve`) or implement custom approving controller like
  [kubelet-rubber-stamp](https://github.com/kontena/kubelet-rubber-stamp).
* *node_labels* - Labels applied to nodes via kubelet --node-labels parameter.
  For example, labels can be set in the inventory as variables or more widely in group_vars.
  *node_labels* can only be defined as a dict:

```yml
node_labels:
  label1_name: label1_value
  label2_name: label2_value
```

* *node_taints* - Taints applied to nodes via kubelet --register-with-taints parameter.
  For example, taints can be set in the inventory as variables or more widely in group_vars.
  *node_taints* has to be defined as a list of strings in format `key=value:effect`, e.g.:

```yml
node_taints:
  - "node.example.com/external=true:NoSchedule"
```

* *podsecuritypolicy_enabled* - When set to `true`, enables the PodSecurityPolicy admission controller and defines two policies `privileged` (applying to all resources in `kube-system` namespace and kubelet) and `restricted` (applying all other namespaces).
  Addons deployed in kube-system namespaces are handled.
* *kubernetes_audit* - When set to `true`, enables Auditing.
  The auditing parameters can be tuned via the following variables (which default values are shown below):
  * `audit_log_path`: /var/log/audit/kube-apiserver-audit.log
  * `audit_log_maxage`: 30
  * `audit_log_maxbackups`: 1
  * `audit_log_maxsize`: 100
  * `audit_policy_file`: "{{ kube_config_dir }}/audit-policy/apiserver-audit-policy.yaml"

  By default, the `audit_policy_file` contains [default rules](https://github.com/kubernetes-sigs/kubespray/blob/master/roles/kubernetes/control-plane/templates/apiserver-audit-policy.yaml.j2) that can be overridden with the `audit_policy_custom_rules` variable.
* *kubernetes_audit_webhook* - When set to `true`, enables the webhook audit backend.
  The webhook parameters can be tuned via the following variables (which default values are shown below):
  * `audit_webhook_config_file`: "{{ kube_config_dir }}/audit-policy/apiserver-audit-webhook-config.yaml"
  * `audit_webhook_server_url`: `"https://audit.app"`
  * `audit_webhook_server_extra_args`: {}
  * `audit_webhook_mode`: batch
  * `audit_webhook_batch_max_size`: 100
  * `audit_webhook_batch_max_wait`: 1s

### Custom flags for Kube Components

For all kube components, custom flags can be passed in. This allows for edge cases where users need changes to the default deployment that may not be applicable to all deployments.

Extra flags for the kubelet can be specified using these variables,
in the form of dicts of key-value pairs of configuration parameters that will be inserted into the kubelet YAML config file. The `kubelet_node_config_extra_args` apply kubelet settings only to nodes and not control planes. Example:

```yml
kubelet_config_extra_args:
  evictionHard:
    memory.available: "100Mi"
  evictionSoftGracePeriod:
    memory.available: "30s"
  evictionSoft:
    memory.available: "300Mi"
```

The possible vars are:

* *kubelet_config_extra_args*
* *kubelet_node_config_extra_args*

Previously, the same parameters could be passed as flags to kubelet binary with the following vars:

* *kubelet_custom_flags*
* *kubelet_node_custom_flags*

The `kubelet_node_custom_flags` apply kubelet settings only to nodes and not control planes. Example:

```yml
kubelet_custom_flags:
  - "--eviction-hard=memory.available<100Mi"
  - "--eviction-soft-grace-period=memory.available=30s"
  - "--eviction-soft=memory.available<300Mi"
```

This alternative is deprecated and will remain until the flags are completely removed from kubelet

Extra flags for the API server, controller, and scheduler components can be specified using these variables,
in the form of dicts of key-value pairs of configuration parameters that will be inserted into the kubeadm YAML config file:

* *kube_kubeadm_apiserver_extra_args*
* *kube_kubeadm_controller_extra_args*
* *kube_kubeadm_scheduler_extra_args*

## App variables

* *helm_version* - Only supports v3.x. Existing v2 installs (with Tiller) will not be modified and need to be removed manually.
