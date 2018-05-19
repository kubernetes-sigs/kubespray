
resource "openstack_compute_keypair_v2" "k8s" {
  name       = "kubernetes-${var.cluster_name}"
  public_key = "${chomp(file(var.public_key_path))}"
}

