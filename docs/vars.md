Configurable Parameters in Kargo
================================

#### Generic Ansible variables

You can view facts gathered by Ansible automatically
[here](http://docs.ansible.com/ansible/playbooks_variables.html#information-discovered-from-systems-facts).

Some variables of note include:

* *ansible_user*: user to connect to via SSH
* *ansible_default_ipv4.address*: IP address Ansible automatically chooses.
  Generated based on the output from the command ``ip -4 route get 8.8.8.8``

#### Common vars that are used in Kargo

* *calico_version* - Specify version of Calico to use
* *calico_cni_version* - Specify version of Calico CNI plugin to use
* *docker_version* - Specify version of Docker to used (should be quoted
  string)
* *etcd_version* - Specify version of ETCD to use
* *ipip* - Enables Calico ipip encapsulation by default
* *hyperkube_image_repo* - Specify the Docker repository where Hyperkube
  resides
* *hyperkube_image_tag* - Specify the Docker tag where Hyperkube resides
* *kube_network_plugin* - Sets k8s network plugin (default Calico)
* *kube_proxy_mode* - Changes k8s proxy mode to iptables mode
* *kube_version* - Specify a given Kubernetes hyperkube version
* *searchdomains* - Array of DNS domains to search when looking up hostnames
* *nameservers* - Array of nameservers to use for DNS lookup

#### Addressing variables

* *ip* - IP to use for binding services (host var)
* *access_ip* - IP for other hosts to use to connect to. Often required when
  deploying from a cloud, such as OpenStack or GCE and you have separate
  public/floating and private IPs.
* *ansible_default_ipv4.address* - Not Kargo-specific, but it is used if ip
  and access_ip are undefined
* *loadbalancer_apiserver* - If defined, all hosts will connect to this
  address instead of localhost for kube-masters and kube-master[0] for
  kube-nodes. See more details in the
  [HA guide](https://github.com/kubernetes-incubator/kargo/blob/master/docs/ha-mode.md).
* *loadbalancer_apiserver_localhost* - makes all hosts to connect to
  the apiserver internally load balanced endpoint. Mutual exclusive to the
  `loadbalancer_apiserver`. See more details in the
  [HA guide](https://github.com/kubernetes-incubator/kargo/blob/master/docs/ha-mode.md).

#### Cluster variables

Kubernetes needs some parameters in order to get deployed. These are the
following default cluster paramters:

* *cluster_name* - Name of cluster (default is cluster.local)
* *domain_name* - Name of cluster DNS domain (default is cluster.local)
* *kube_network_plugin* - Plugin to use for container networking
* *kube_service_addresses* - Subnet for cluster IPs (default is
  10.233.0.0/18). Must not overlap with kube_pods_subnet
* *kube_pods_subnet* - Subnet for Pod IPs (default is 10.233.64.0/18). Must not
  overlap with kube_service_addresses.
* *kube_network_node_prefix* - Subnet allocated per-node for pod IPs. Remainin
  bits in kube_pods_subnet dictates how many kube-nodes can be in cluster.
* *dns_setup* - Enables dnsmasq
* *dns_server* - Cluster IP for dnsmasq (default is 10.233.0.2)
* *skydns_server* - Cluster IP for KubeDNS (default is 10.233.0.3)
* *cloud_provider* - Enable extra Kubelet option if operating inside GCE or
  OpenStack (default is unset)
* *kube_hostpath_dynamic_provisioner* - Required for use of PetSets type in
  Kubernetes

Note, if cloud providers have any use of the ``10.233.0.0/16``, like instances'
private addresses, make sure to pick another values for ``kube_service_addresses``
and ``kube_pods_subnet``, for example from the ``172.18.0.0/16``.

#### DNS variables

By default, dnsmasq gets set up with 8.8.8.8 as an upstream DNS server and all
other settings from your existing /etc/resolv.conf are lost. Set the following
variables to match your requirements.

* *upstream_dns_servers* - Array of upstream DNS servers configured on host in
  addition to Kargo deployed DNS
* *nameservers* - Array of DNS servers configured for use in dnsmasq
* *searchdomains* - Array of up to 4 search domains
* *skip_dnsmasq* - Don't set up dnsmasq (use only KubeDNS)

For more information, see [DNS
Stack](https://github.com/kubernetes-incubator/kargo/blob/master/docs/dns-stack.md).

#### Other service variables

* *docker_options* - Commonly used to set
  ``--insecure-registry=myregistry.mydomain:5000``
* *http_proxy/https_proxy/no_proxy* - Proxy variables for deploying behind a
  proxy
* *kubelet_load_modules* - For some things, kubelet needs to load kernel modules.  For example,
  dynamic kernel services are needed for mounting persistent volumes into containers.  These may not be
  loaded by preinstall kubernetes processes.  For example, ceph and rbd backed volumes.  Set this variable to
  true to let kubelet load kernel modules.

##### Custom flags for Kube Components
For all kube components, custom flags can be passed in. This allows for edge cases where users need changes to the default deployment that may not be applicable to all deployments. This can be done by providing a list of flags. Example:
```
kubelet_custom_flags:
  - "--eviction-hard=memory.available<100Mi"
  - "--eviction-soft-grace-period=memory.available=30s"
  - "--eviction-soft=memory.available<300Mi"
```
The possible vars are:
* *apiserver_custom_flags*
* *controller_mgr_custom_flags*
* *scheduler_custom_flags*
* *kubelet_custom_flags*

#### User accounts

Kargo sets up two Kubernetes accounts by default: ``root`` and ``kube``. Their
passwords default to changeme. You can set this by changing ``kube_api_pwd``.
