# Configure the Equinix Metal Provider
provider "metal" {
}

resource "metal_ssh_key" "k8s" {
  count      = var.public_key_path != "" ? 1 : 0
  name       = "kubernetes-${var.cluster_name}"
  public_key = chomp(file(var.public_key_path))
}

resource "metal_device" "k8s_master" {
  depends_on = [metal_ssh_key.k8s]

  count            = var.number_of_k8s_masters
  hostname         = "${var.cluster_name}-k8s-master-${count.index + 1}"
  plan             = var.plan_k8s_masters
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.metal_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_control_plane", "etcd", "kube_node"]
}

resource "metal_device" "k8s_master_no_etcd" {
  depends_on = [metal_ssh_key.k8s]

  count            = var.number_of_k8s_masters_no_etcd
  hostname         = "${var.cluster_name}-k8s-master-${count.index + 1}"
  plan             = var.plan_k8s_masters_no_etcd
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.metal_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_control_plane"]
}

resource "metal_device" "k8s_etcd" {
  depends_on = [metal_ssh_key.k8s]

  count            = var.number_of_etcd
  hostname         = "${var.cluster_name}-etcd-${count.index + 1}"
  plan             = var.plan_etcd
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.metal_project_id
  tags             = ["cluster-${var.cluster_name}", "etcd"]
}

resource "metal_device" "k8s_node" {
  depends_on = [metal_ssh_key.k8s]

  count            = var.number_of_k8s_nodes
  hostname         = "${var.cluster_name}-k8s-node-${count.index + 1}"
  plan             = var.plan_k8s_nodes
  facilities       = [var.facility]
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.metal_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_node"]
}

