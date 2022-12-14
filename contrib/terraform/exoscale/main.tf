provider "exoscale" {}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"

  prefix   = var.prefix
  zone     = var.zone
  machines = var.machines

  ssh_public_keys = var.ssh_public_keys

  ssh_whitelist        = var.ssh_whitelist
  api_server_whitelist = var.api_server_whitelist
  nodeport_whitelist   = var.nodeport_whitelist
}

#
# Generate ansible inventory
#

data "template_file" "inventory" {
  template = file("${path.module}/templates/inventory.tpl")

  vars = {
    connection_strings_master = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s ip=%s etcd_member_name=etcd%d",
      keys(module.kubernetes.master_ip_addresses),
      values(module.kubernetes.master_ip_addresses).*.public_ip,
      values(module.kubernetes.master_ip_addresses).*.private_ip,
    range(1, length(module.kubernetes.master_ip_addresses) + 1)))
    connection_strings_worker = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s ip=%s",
      keys(module.kubernetes.worker_ip_addresses),
      values(module.kubernetes.worker_ip_addresses).*.public_ip,
    values(module.kubernetes.worker_ip_addresses).*.private_ip))

    list_master       = join("\n", keys(module.kubernetes.master_ip_addresses))
    list_worker       = join("\n", keys(module.kubernetes.worker_ip_addresses))
    api_lb_ip_address = module.kubernetes.control_plane_lb_ip_address
  }
}

resource "null_resource" "inventories" {
  provisioner "local-exec" {
    command = "echo '${data.template_file.inventory.rendered}' > ${var.inventory_file}"
  }

  triggers = {
    template = data.template_file.inventory.rendered
  }
}
