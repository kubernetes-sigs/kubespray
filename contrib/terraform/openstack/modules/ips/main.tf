resource "null_resource" "dummy_dependency" {
  triggers = {
    dependency_id = var.router_id
  }
}

resource "openstack_networking_floatingip_v2" "k8s_master" {
  count      = var.number_of_k8s_masters
  pool       = var.floatingip_pool
  depends_on = [null_resource.dummy_dependency]
}

resource "openstack_networking_floatingip_v2" "k8s_master_no_etcd" {
  count      = var.number_of_k8s_masters_no_etcd
  pool       = var.floatingip_pool
  depends_on = [null_resource.dummy_dependency]
}

resource "openstack_networking_floatingip_v2" "k8s_node" {
  count      = var.number_of_k8s_nodes
  pool       = var.floatingip_pool
  depends_on = [null_resource.dummy_dependency]
}

resource "openstack_networking_floatingip_v2" "bastion" {
  count      = var.number_of_bastions
  pool       = var.floatingip_pool
  depends_on = [null_resource.dummy_dependency]
}

resource "openstack_networking_floatingip_v2" "k8s_nodes" {
  for_each   = var.number_of_k8s_nodes == 0 ? { for key, value in var.k8s_nodes : key => value if value.floating_ip } : {}
  pool       = var.floatingip_pool
  depends_on = [null_resource.dummy_dependency]
}

