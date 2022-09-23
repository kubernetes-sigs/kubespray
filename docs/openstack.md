
# OpenStack

## Known compatible public clouds

Kubespray has been tested on a number of OpenStack Public Clouds including (in alphabetical order):

- [Auro](https://auro.io/)
- [Betacloud](https://www.betacloud.io/)
- [CityCloud](https://www.citycloud.com/)
- [DreamHost](https://www.dreamhost.com/cloud/computing/)
- [ELASTX](https://elastx.se/)
- [EnterCloudSuite](https://www.entercloudsuite.com/)
- [FugaCloud](https://fuga.cloud/)
- [Infomaniak](https://infomaniak.com)
- [Open Telekom Cloud](https://cloud.telekom.de/) : requires to set the variable `wait_for_floatingip = "true"` in your cluster.tfvars
- [OVHcloud](https://www.ovhcloud.com/)
- [Rackspace](https://www.rackspace.com/)
- [Ultimum](https://ultimum.io/)
- [VexxHost](https://vexxhost.com/)
- [Zetta](https://www.zetta.io/)

## The in-tree cloud provider

To deploy Kubespray on [OpenStack](https://www.openstack.org/) uncomment the `cloud_provider` option in `group_vars/all/all.yml` and set it to `openstack`.

After that make sure to source in your OpenStack credentials like you would do when using `nova-client` or `neutron-client` by using `source path/to/your/openstack-rc` or `. path/to/your/openstack-rc`.

For those who prefer to pass the OpenStack CA certificate as a string, one can
base64 encode the cacert file and store it in the variable `openstack_cacert`.

The next step is to make sure the hostnames in your `inventory` file are identical to your instance names in OpenStack.
Otherwise [cinder](https://wiki.openstack.org/wiki/Cinder) won't work as expected.

Unless you are using calico or kube-router you can now run the playbook.

## The external cloud provider

The in-tree cloud provider is deprecated and will be removed in a future version of Kubernetes. The target release for removing all remaining in-tree cloud providers is set to 1.21.

The new cloud provider is configured to have Octavia by default in Kubespray.

- Enable the new external cloud provider in `group_vars/all/all.yml`:

  ```yaml
  cloud_provider: external
  external_cloud_provider: openstack
  ```

- Enable Cinder CSI in `group_vars/all/openstack.yml`:

  ```yaml
  cinder_csi_enabled: true
  ```

- Enable topology support (optional), if your openstack provider has custom Zone names you can override the default "nova" zone by setting the variable `cinder_topology_zones`

  ```yaml
  cinder_topology: true
  ```

- Enabling `cinder_csi_ignore_volume_az: true`, ignores volumeAZ and schedules on any of the available node AZ.

  ```yaml
  cinder_csi_ignore_volume_az: true
  ```

- If you are using OpenStack loadbalancer(s) replace the `openstack_lbaas_subnet_id` with the new `external_openstack_lbaas_subnet_id`. **Note** The new cloud provider is using Octavia instead of Neutron LBaaS by default!
- Enable 3 feature gates to allow migration of all volumes and storage classes (if you have any feature gates already set just add the 3 listed below):

  ```yaml
  kube_feature_gates:
  - CSIMigration=true
  - CSIMigrationOpenStack=true
  - ExpandCSIVolumes=true
  ```

- If you are in a case of a multi-nic OpenStack VMs (see [kubernetes/cloud-provider-openstack#407](https://github.com/kubernetes/cloud-provider-openstack/issues/407) and [#6083](https://github.com/kubernetes-sigs/kubespray/issues/6083) for explanation), you should override the default OpenStack networking configuration:

  ```yaml
  external_openstack_network_ipv6_disabled: false
  external_openstack_network_internal_networks: []
  external_openstack_network_public_networks: []
  ```

- You can override the default OpenStack metadata configuration (see [#6338](https://github.com/kubernetes-sigs/kubespray/issues/6338) for explanation):

  ```yaml
  external_openstack_metadata_search_order: "configDrive,metadataService"
  ```

- Available variables for configuring lbaas:

  ```yaml
  external_openstack_lbaas_create_monitor: false
  external_openstack_lbaas_monitor_delay: "1m"
  external_openstack_lbaas_monitor_timeout: "30s"
  external_openstack_lbaas_monitor_max_retries: "3"
  external_openstack_lbaas_provider: octavia
  external_openstack_lbaas_use_octavia: false
  external_openstack_lbaas_network_id: "Neutron network ID to create LBaaS VIP"
  external_openstack_lbaas_subnet_id: "Neutron subnet ID to create LBaaS VIP"
  external_openstack_lbaas_floating_network_id: "Neutron network ID to get floating IP from"
  external_openstack_lbaas_floating_subnet_id: "Neutron subnet ID to get floating IP from"
  external_openstack_lbaas_method: "ROUND_ROBIN"
  external_openstack_lbaas_manage_security_groups: false
  external_openstack_lbaas_internal_lb: false

  ```

- Run `source path/to/your/openstack-rc` to read your OpenStack credentials like `OS_AUTH_URL`, `OS_USERNAME`, `OS_PASSWORD`, etc. Those variables are used for accessing OpenStack from the external cloud provider.
- Run the `cluster.yml` playbook

## Additional step needed when using calico or kube-router

Being L3 CNI, calico and kube-router do not encapsulate all packages with the hosts' ip addresses. Instead the packets will be routed with the PODs ip addresses directly.

OpenStack will filter and drop all packets from ips it does not know to prevent spoofing.

In order to make L3 CNIs work on OpenStack you will need to tell OpenStack to allow pods packets by allowing the network they use.

First you will need the ids of your OpenStack instances that will run kubernetes:

  ```bash
  openstack server list --project YOUR_PROJECT
  +--------------------------------------+--------+----------------------------------+--------+-------------+
  | ID                                   | Name   | Tenant ID                        | Status | Power State |
  +--------------------------------------+--------+----------------------------------+--------+-------------+
  | e1f48aad-df96-4bce-bf61-62ae12bf3f95 | k8s-1  | fba478440cb2444a9e5cf03717eb5d6f | ACTIVE | Running     |
  | 725cd548-6ea3-426b-baaa-e7306d3c8052 | k8s-2  | fba478440cb2444a9e5cf03717eb5d6f | ACTIVE | Running     |
  ```

Then you can use the instance ids to find the connected [neutron](https://wiki.openstack.org/wiki/Neutron) ports (though they are now configured through using OpenStack):

  ```bash
  openstack port list -c id -c device_id --project YOUR_PROJECT
  +--------------------------------------+--------------------------------------+
  | id                                   | device_id                            |
  +--------------------------------------+--------------------------------------+
  | 5662a4e0-e646-47f0-bf88-d80fbd2d99ef | e1f48aad-df96-4bce-bf61-62ae12bf3f95 |
  | e5ae2045-a1e1-4e99-9aac-4353889449a7 | 725cd548-6ea3-426b-baaa-e7306d3c8052 |
  ```

Given the port ids on the left, you can set the two `allowed-address`(es) in OpenStack. Note that you have to allow both `kube_service_addresses` (default `10.233.0.0/18`) and `kube_pods_subnet` (default `10.233.64.0/18`.)

  ```bash
  # allow kube_service_addresses and kube_pods_subnet network
  openstack port set 5662a4e0-e646-47f0-bf88-d80fbd2d99ef --allowed-address ip-address=10.233.0.0/18 --allowed-address ip-address=10.233.64.0/18
  openstack port set e5ae2045-a1e1-4e99-9aac-4353889449a7 --allowed-address ip-address=10.233.0.0/18 --allowed-address ip-address=10.233.64.0/18
  ```

If all the VMs in the tenant correspond to Kubespray deployment, you can "sweep run" above with:

  ```bash
  openstack port list --device-owner=compute:nova -c ID -f value | xargs -tI@ openstack port set @ --allowed-address ip-address=10.233.0.0/18 --allowed-address ip-address=10.233.64.0/18
  ```

Now you can finally run the playbook.
