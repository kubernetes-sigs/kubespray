
resource "openstack_compute_instance_v2" "etcd" {
  name       = "${var.cluster_name}-etcd-${count.index+1}"
  count      = "${var.number_of_etcd}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_etcd}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = ["${openstack_compute_secgroup_v2.k8s.name}"]

  metadata {
    ssh_user = "${var.ssh_user}"
    kubespray_groups = "etcd,vault,no-floating"
    depends_on = "${var.network_id}"
  }

}
