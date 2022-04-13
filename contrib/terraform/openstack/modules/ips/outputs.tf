# If k8s_master_fips is already defined as input, keep the same value since new FIPs have not been created.
output "k8s_master_fips" {
  value = length(var.k8s_master_fips) > 0 ? var.k8s_master_fips : openstack_networking_floatingip_v2.k8s_master[*].address
}

output "k8s_masters_fips" {
  value = openstack_networking_floatingip_v2.k8s_masters
}

# If k8s_master_fips is already defined as input, keep the same value since new FIPs have not been created.
output "k8s_master_no_etcd_fips" {
  value = length(var.k8s_master_fips) > 0 ? var.k8s_master_fips : openstack_networking_floatingip_v2.k8s_master_no_etcd[*].address
}

output "k8s_node_fips" {
  value = openstack_networking_floatingip_v2.k8s_node[*].address
}

output "k8s_nodes_fips" {
  value = openstack_networking_floatingip_v2.k8s_nodes
}

output "bastion_fips" {
  value = length(var.bastion_fips) > 0 ? var.bastion_fips : openstack_networking_floatingip_v2.bastion[*].address
}
