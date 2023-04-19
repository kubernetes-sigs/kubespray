provider "hcloud" {}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"
  # source = "./modules/kubernetes-cluster-flatcar"

  prefix = var.prefix

  zone = var.zone

  machines = var.machines

  #only for flatcar
  #ssh_private_key_path = var.ssh_private_key_path

  ssh_public_keys = var.ssh_public_keys
  network_zone    = var.network_zone

  ssh_whitelist        = var.ssh_whitelist
  api_server_whitelist = var.api_server_whitelist
  nodeport_whitelist   = var.nodeport_whitelist
  ingress_whitelist    = var.ingress_whitelist
}

#
# Generate ansible inventory
#

locals {
  inventory = templatefile(
    "${path.module}/templates/inventory.tpl",
    {
      connection_strings_master = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s ip=%s etcd_member_name=etcd%d",
        keys(module.kubernetes.master_ip_addresses),
        values(module.kubernetes.master_ip_addresses).*.public_ip,
        values(module.kubernetes.master_ip_addresses).*.private_ip,
      range(1, length(module.kubernetes.master_ip_addresses) + 1)))
      connection_strings_worker = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s ip=%s",
        keys(module.kubernetes.worker_ip_addresses),
        values(module.kubernetes.worker_ip_addresses).*.public_ip,
      values(module.kubernetes.worker_ip_addresses).*.private_ip))
      list_master = join("\n", keys(module.kubernetes.master_ip_addresses))
      list_worker = join("\n", keys(module.kubernetes.worker_ip_addresses))
      network_id  = module.kubernetes.network_id
    }
  )
}

resource "null_resource" "inventories" {
  provisioner "local-exec" {
    command = "echo '${local.inventory}' > ${var.inventory_file}"
  }

  triggers = {
    template = local.inventory
  }
}
