output "router_id" {
  value = "${openstack_networking_router_interface_v2.k8s.id}"
}

output "network_id" {
  value = "${openstack_networking_subnet_v2.k8s.id}"
}
