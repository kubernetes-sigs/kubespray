
resource "openstack_compute_instance_v2" "k8s_master" {
  name       = "${var.cluster_name}-k8s-master-${count.index+1}"
  count      = "${var.number_of_k8s_masters}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_k8s_master}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s_master.name}",
    "${openstack_compute_secgroup_v2.bastion.name}",
    "${openstack_compute_secgroup_v2.k8s.name}",
    "default",
  ]

  metadata {
    ssh_user         = "${var.ssh_user}"
    kubespray_groups = "etcd,kube-master,k8s-cluster,vault"
    depends_on       = "${var.network_id}"
  }

}


resource "openstack_compute_instance_v2" "k8s_master_no_etcd" {
  name       = "${var.cluster_name}-k8s-master-ne-${count.index+1}"
  count      = "${var.number_of_k8s_masters_no_etcd}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_k8s_master}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s_master.name}",
    "${openstack_compute_secgroup_v2.k8s.name}",
  ]

  metadata {
    ssh_user         = "${var.ssh_user}"
    kubespray_groups = "kube-master,k8s-cluster,vault"
    depends_on       = "${var.network_id}"
  }

}


resource "openstack_compute_instance_v2" "k8s_master_no_floating_ip" {
  name       = "${var.cluster_name}-k8s-master-nf-${count.index+1}"
  count      = "${var.number_of_k8s_masters_no_floating_ip}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_k8s_master}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s_master.name}",
    "${openstack_compute_secgroup_v2.k8s.name}",
    "default",
  ]

  metadata {
    ssh_user         = "${var.ssh_user}"
    kubespray_groups = "etcd,kube-master,k8s-cluster,vault,no-floating"
    depends_on       = "${var.network_id}"
  }

}


resource "openstack_compute_instance_v2" "k8s_master_no_floating_ip_no_etcd" {
  name       = "${var.cluster_name}-k8s-master-ne-nf-${count.index+1}"
  count      = "${var.number_of_k8s_masters_no_floating_ip_no_etcd}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_k8s_master}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s_master.name}",
    "${openstack_compute_secgroup_v2.k8s.name}",
  ]

  metadata {
    ssh_user         = "${var.ssh_user}"
    kubespray_groups = "kube-master,k8s-cluster,vault,no-floating"
    depends_on       = "${var.network_id}"
  }

}


resource "openstack_compute_floatingip_associate_v2" "k8s_master" {
  count       = "${var.number_of_k8s_masters}"
  instance_id = "${element(openstack_compute_instance_v2.k8s_master.*.id, count.index)}"
  floating_ip = "${var.k8s_master_fips[count.index]}"
}
