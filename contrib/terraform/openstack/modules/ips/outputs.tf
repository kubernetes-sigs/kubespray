output "k8s_master_fips" {
  value = openstack_networking_floatingip_v2.k8s_master[*].address
}

output "k8s_master_no_etcd_fips" {
  value = openstack_networking_floatingip_v2.k8s_master_no_etcd[*].address
}

output "k8s_node_fips" {
  value = openstack_networking_floatingip_v2.k8s_node[*].address
}

output "k8s_nodes_fips" {
  value = openstack_networking_floatingip_v2.k8s_nodes
}

output "bastion_fips" {
  value = openstack_networking_floatingip_v2.bastion[*].address
}
