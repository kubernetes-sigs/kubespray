
resource "openstack_blockstorage_volume_v2" "glusterfs_volume" {
  name        = "${var.cluster_name}-glusterfs_volume-${count.index+1}"
  count       = "${var.number_of_gfs_nodes_no_floating_ip}"
  description = "Non-ephemeral volume for GlusterFS"
  size        = "${var.gfs_volume_size_in_gb}"
}


resource "openstack_compute_instance_v2" "glusterfs_node_no_floating_ip" {
  name       = "${var.cluster_name}-gfs-node-nf-${count.index+1}"
  count      = "${var.number_of_gfs_nodes_no_floating_ip}"
  image_name = "${var.image_gfs}"
  flavor_id  = "${var.flavor_gfs_node}"
  key_pair   = "${openstack_compute_keypair_v2.k8s.name}"

  network {
    name = "${var.network_name}"
  }

  security_groups = [
    "${openstack_compute_secgroup_v2.k8s.name}",
    "default",
  ]

  metadata {
    ssh_user         = "${var.ssh_user_gfs}"
    kubespray_groups = "gfs-cluster,network-storage,no-floating"
    depends_on       = "${var.network_id}"
  }

}


resource "openstack_compute_volume_attach_v2" "glusterfs_volume" {
  count       = "${var.number_of_gfs_nodes_no_floating_ip}"
  instance_id = "${element(openstack_compute_instance_v2.glusterfs_node_no_floating_ip.*.id, count.index)}"
  volume_id   = "${element(openstack_blockstorage_volume_v2.glusterfs_volume.*.id, count.index)}"
}
