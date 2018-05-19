
resource "openstack_compute_instance_v2" "k8s_node" {
  name       = "${var.cluster_name}-k8s-node-${count.index+1}"
  count      = "${var.number_of_k8s_nodes}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_k8s_node}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s.name}",
    "${openstack_compute_secgroup_v2.bastion.name}",
    "default",
  ]

  metadata {
    ssh_user         = "${var.ssh_user}"
    kubespray_groups = "kube-node,k8s-cluster"
    depends_on       = "${var.network_id}"
  }

  provisioner "local-exec" {
    command = "sed s/USER/${var.ssh_user}/ contrib/terraform/openstack/ansible_bastion_template.txt | sed s/BASTION_ADDRESS/${element( concat(var.bastion_fips, var.k8s_node_fips), 0)}/ > contrib/terraform/group_vars/no-floating.yml"
  }

}


resource "openstack_compute_instance_v2" "k8s_node_no_floating_ip" {
  name       = "${var.cluster_name}-k8s-node-nf-${count.index+1}"
  count      = "${var.number_of_k8s_nodes_no_floating_ip}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_k8s_node}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s.name}",
    "default",
  ]

  metadata {
    ssh_user         = "${var.ssh_user}"
    kubespray_groups = "kube-node,k8s-cluster,no-floating"
    depends_on       = "${var.network_id}"
  }

}


resource "openstack_compute_floatingip_associate_v2" "k8s_node" {
  count       = "${var.number_of_k8s_nodes}"
  floating_ip = "${var.k8s_node_fips[count.index]}"
  instance_id = "${element(openstack_compute_instance_v2.k8s_node.*.id, count.index)}"
}
