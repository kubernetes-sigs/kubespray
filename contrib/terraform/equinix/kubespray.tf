resource "equinix_metal_ssh_key" "k8s" {
  count      = var.public_key_path != "" ? 1 : 0
  name       = "kubernetes-${var.cluster_name}"
  public_key = chomp(file(var.public_key_path))
}

resource "equinix_metal_device" "k8s_master" {
  depends_on = [equinix_metal_ssh_key.k8s]

  count            = var.number_of_k8s_masters
  hostname         = "${var.cluster_name}-k8s-master-${count.index + 1}"
  plan             = var.plan_k8s_masters
  metro            = var.metro
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.equinix_metal_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_control_plane", "etcd", "kube_node"]
}

resource "equinix_metal_device" "k8s_master_no_etcd" {
  depends_on = [equinix_metal_ssh_key.k8s]

  count            = var.number_of_k8s_masters_no_etcd
  hostname         = "${var.cluster_name}-k8s-master-${count.index + 1}"
  plan             = var.plan_k8s_masters_no_etcd
  metro            = var.metro
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.equinix_metal_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_control_plane"]
}

resource "equinix_metal_device" "k8s_etcd" {
  depends_on = [equinix_metal_ssh_key.k8s]

  count            = var.number_of_etcd
  hostname         = "${var.cluster_name}-etcd-${count.index + 1}"
  plan             = var.plan_etcd
  metro            = var.metro
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.equinix_metal_project_id
  tags             = ["cluster-${var.cluster_name}", "etcd"]
}

resource "equinix_metal_device" "k8s_node" {
  depends_on = [equinix_metal_ssh_key.k8s]

  count            = var.number_of_k8s_nodes
  hostname         = "${var.cluster_name}-k8s-node-${count.index + 1}"
  plan             = var.plan_k8s_nodes
  metro            = var.metro
  operating_system = var.operating_system
  billing_cycle    = var.billing_cycle
  project_id       = var.equinix_metal_project_id
  tags             = ["cluster-${var.cluster_name}", "k8s_cluster", "kube_node"]
}
