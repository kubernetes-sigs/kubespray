
resource "openstack_compute_instance_v2" "bastion" {
  name       = "${var.cluster_name}-bastion-${count.index+1}"
  count      = "${var.number_of_bastions}"
  image_name = "${var.image}"
  flavor_id  = "${var.flavor_bastion}"
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
    kubespray_groups = "bastion"
    depends_on       = "${var.network_id}"
  }

  provisioner "local-exec" {
    command = "sed s/USER/${var.ssh_user}/ contrib/terraform/openstack/ansible_bastion_template.txt | sed s/BASTION_ADDRESS/${var.bastion_fips[0]}/ > contrib/terraform/openstack/group_vars/no-floating.yml"
  }

}


resource "openstack_compute_floatingip_associate_v2" "bastion" {
  count       = "${var.number_of_bastions}"
  floating_ip = "${var.bastion_fips[count.index]}"
  instance_id = "${element(openstack_compute_instance_v2.bastion.*.id, count.index)}"
}
