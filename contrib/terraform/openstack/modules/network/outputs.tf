output "router_id" {
  value = "${element(concat(openstack_networking_router_v2.k8s.*.id, list("")), 0)}"
}

output "router_internal_port_id" {
  value = "${element(concat(openstack_networking_router_interface_v2.k8s.*.id, list("")), 0)}"

}

output "subnet_id" {
  value = "${element(concat(openstack_networking_subnet_v2.k8s.*.id, list("")), 0)}"
}

output "bastion_network_id" {
  value = "${element(data.openstack_networking_network_v2.bastion_network.*.id, 0)}"
}
