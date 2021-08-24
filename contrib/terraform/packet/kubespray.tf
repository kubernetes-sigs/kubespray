# Configure the Equinix Metal Provider
provider "packet" {
  version = "~> 2.0"
}

resource "packet_ssh_key" "k8s" {
  count      = var.public_key_path != "" ? 1 : 0
  name       = "kubernetes-${var.cluster_name}"
  public_key = chomp(file(var.public_key_path))
}

resource "packet_device" "k8s_master" {
  depends_on = [packet_ssh_key.k8s]

  count            = var.number_of_k8s_masters
  hostname         = "${var.cluster_name}-k8s-master-${count.index + 1}"
  plan             = var.plan_k8s_masters
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.packet_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_control_plane", "etcd", "kube_node"]
}

resource "packet_device" "k8s_master_no_etcd" {
  depends_on = [packet_ssh_key.k8s]

  count            = var.number_of_k8s_masters_no_etcd
  hostname         = "${var.cluster_name}-k8s-master-${count.index + 1}"
  plan             = var.plan_k8s_masters_no_etcd
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.packet_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_control_plane"]
}

resource "packet_device" "k8s_etcd" {
  depends_on = [packet_ssh_key.k8s]

  count            = var.number_of_etcd
  hostname         = "${var.cluster_name}-etcd-${count.index + 1}"
  plan             = var.plan_etcd
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.packet_project_id
  tags             = ["cluster-${var.cluster_name}", "etcd"]
}

resource "packet_device" "k8s_node" {
  depends_on = [packet_ssh_key.k8s]

  count            = var.number_of_k8s_nodes
  hostname         = "${var.cluster_name}-k8s-node-${count.index + 1}"
  plan             = var.plan_k8s_nodes
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.packet_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_node"]
}

