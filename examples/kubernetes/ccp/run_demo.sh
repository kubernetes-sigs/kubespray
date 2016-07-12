# This script should be executed inside k8s:
# docker run -t -i 127.0.0.1:31500/mcp/nova-base /bin/bash

export OS_USERNAME=admin
export OS_PASSWORD=password
export OS_TENANT_NAME=admin
export OS_REGION_NAME=RegionOne
export OS_AUTH_URL=http://keystone:35357

# Key
nova keypair-add test > test.pem
chmod 600 test.pem

# Flavor
nova flavor-create demo --is-public true auto 128 2 1

# Image
curl -O http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img
glance image-create --name cirros --disk-format qcow2 --container-format bare --file cirros-0.3.4-x86_64-disk.img

# Network
neutron net-create net1 --provider:network-type vxlan
neutron subnet-create net1 172.20.0.0/24 --name subnet1

# Aggregates
node2=`openstack hypervisor list | grep -o '[a-z]\+-k8s-02'`
node3=`openstack hypervisor list | grep -o '[a-z]\+-k8s-03'`
nova aggregate-create n2 n2
nova aggregate-add-host n2 $node2
nova aggregate-create n3 n3
nova aggregate-add-host n3 $node3

# Instances
net_id=`neutron net-list | grep net1 | awk '{print $2}'`
nova boot ti02 --image cirros --flavor demo --nic net-id=$net_id --key-name test --availability-zone n2
nova boot ti03 --image cirros --flavor demo --nic net-id=$net_id --key-name test --availability-zone n3
