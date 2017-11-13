resource "openstack_networking_floatingip_v2" "k8s_master" {
    count = "${var.number_of_k8s_masters + var.number_of_k8s_masters_no_etcd}"
    pool = "${var.floatingip_pool}"
}

resource "openstack_networking_floatingip_v2" "k8s_node" {
    count = "${var.number_of_k8s_nodes}"
    pool = "${var.floatingip_pool}"
}
