OpenStack
===============

To deploy kubespray on [OpenStack](https://www.openstack.org/) uncomment the `cloud_provider` option in `group_vars/all.yml` and set it to `'openstack'`.

After that make sure to source in your OpenStack credentials like you would do when using `nova-client` or `neutron-client` by using `source path/to/your/openstack-rc` or `. path/to/your/openstack-rc`.

For those who prefer to pass the OpenStack CA certificate as a string, one can
base64 encode the cacert file and store it in the variable `openstack_cacert`.

The next step is to make sure the hostnames in your `inventory` file are identical to your instance names in OpenStack.
Otherwise [cinder](https://wiki.openstack.org/wiki/Cinder) won't work as expected.

Unless you are using calico or kube-router you can now run the playbook.

**Additional step needed when using calico or kube-router:**

Being L3 CNI, calico and kube-router do not encapsulate all packages with the hosts' ip addresses. Instead the packets will be routed with the PODs ip addresses directly.

OpenStack will filter and drop all packets from ips it does not know to prevent spoofing.

In order to make L3 CNIs work on OpenStack you will need to tell OpenStack to allow pods packets by allowing the network they use.

First you will need the ids of your OpenStack instances that will run kubernetes:

    openstack server list --project YOUR_PROJECT
    +--------------------------------------+--------+----------------------------------+--------+-------------+
    | ID                                   | Name   | Tenant ID                        | Status | Power State |
    +--------------------------------------+--------+----------------------------------+--------+-------------+
    | e1f48aad-df96-4bce-bf61-62ae12bf3f95 | k8s-1  | fba478440cb2444a9e5cf03717eb5d6f | ACTIVE | Running     |
    | 725cd548-6ea3-426b-baaa-e7306d3c8052 | k8s-2  | fba478440cb2444a9e5cf03717eb5d6f | ACTIVE | Running     |

Then you can use the instance ids to find the connected [neutron](https://wiki.openstack.org/wiki/Neutron) ports (though they are now configured through using OpenStack):

    openstack port list -c id -c device_id --project YOUR_PROJECT
    +--------------------------------------+--------------------------------------+
    | id                                   | device_id                            |
    +--------------------------------------+--------------------------------------+
    | 5662a4e0-e646-47f0-bf88-d80fbd2d99ef | e1f48aad-df96-4bce-bf61-62ae12bf3f95 |
    | e5ae2045-a1e1-4e99-9aac-4353889449a7 | 725cd548-6ea3-426b-baaa-e7306d3c8052 |

Given the port ids on the left, you can set the two `allowed-address`(es) in OpenStack. Note that you have to allow both `kube_service_addresses` (default `10.233.0.0/18`) and `kube_pods_subnet` (default `10.233.64.0/18`.)

    # allow kube_service_addresses and kube_pods_subnet network
    openstack port set 5662a4e0-e646-47f0-bf88-d80fbd2d99ef --allowed-address ip-address=10.233.0.0/18 --allowed-address ip-address=10.233.64.0/18
    openstack port set e5ae2045-a1e1-4e99-9aac-4353889449a7 --allowed-address ip-address=10.233.0.0/18 --allowed-address ip-address=10.233.64.0/18

If all the VMs in the tenant correspond to kubespray deployment, you can "sweep run" above with:

    openstack port list --device-owner=compute:nova -c ID -f value | xargs -tI@ openstack port set @ --allowed-address ip-address=10.233.0.0/18 --allowed-address ip-address=10.233.64.0/18

Now you can finally run the playbook.
