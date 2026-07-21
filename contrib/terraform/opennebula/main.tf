provider "opennebula" {
  # Credentials/endpoint fall back to the OPENNEBULA_* environment variables
  # when the corresponding variable is left empty.
  endpoint = var.one_endpoint != "" ? var.one_endpoint : null
  username = var.one_username != "" ? var.one_username : null
  password = var.one_password != "" ? var.one_password : null
  insecure = var.one_insecure ? true : null
}

data "opennebula_template" "node" {
  name = var.template_name

  lifecycle {
    precondition {
      condition = length([
        for machine in local.machines : machine if machine.node_type == "master"
      ]) > 0
      error_message = "Define at least one control-plane node: set master_count >= 1 or add a machines entry with node_type \"master\"."
    }
  }
}

data "opennebula_virtual_network" "network" {
  name = var.network_name
}

locals {
  # Effective node set: the explicit machines map wins; otherwise it is
  # generated from master_count/worker_count (master-0.., worker-0..).
  machines = length(var.machines) > 0 ? var.machines : merge(
    { for i in range(var.master_count) : "master-${i}" => { node_type = "master", ip = "" } },
    { for i in range(var.worker_count) : "worker-${i}" => { node_type = "worker", ip = "" } },
  )
  # The provider's data source flattens template disks that reference their
  # image by name (IMAGE=) as image_id = -1; treat that sentinel as unusable.
  template_disk_image_id = try(data.opennebula_template.node.disk[0].image_id, -1) >= 0 ? data.opennebula_template.node.disk[0].image_id : null
  # Preserve the template's DISK-level SIZE override when the OS disk has to
  # be re-declared (0 = no override, use the image's size)
  template_disk_size = try(data.opennebula_template.node.disk[0].size, 0)
}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"

  prefix   = var.prefix
  machines = local.machines

  template_id            = data.opennebula_template.node.id
  template_disk_image_id = local.template_disk_image_id
  template_disk_size     = local.template_disk_size
  network_id             = data.opennebula_virtual_network.network.id

  ## Master ##
  master_cpu       = var.master_cpu
  master_vcpu      = var.master_vcpu
  master_memory    = var.master_memory
  master_disk_size = var.master_disk_size

  ## Worker ##
  worker_cpu       = var.worker_cpu
  worker_vcpu      = var.worker_vcpu
  worker_memory    = var.worker_memory
  worker_disk_size = var.worker_disk_size

  ## OpenNebula extras ##
  additional_disk_size         = var.additional_disk_size
  image_datastore_name         = var.image_datastore_name
  masters_anti_affinity        = var.masters_anti_affinity
  network_reservation_size     = var.network_reservation_size
  network_reservation_first_ip = var.network_reservation_first_ip
  network_reservation_ar_id    = var.network_reservation_ar_id

  ssh_public_keys   = var.ssh_public_keys
  vm_create_timeout = var.vm_create_timeout
}

#
# Generate ansible inventory
#

resource "local_file" "inventory" {
  content = templatefile("${path.module}/templates/inventory.tpl", {
    connection_strings_master = join("\n", formatlist("%s ansible_user=${var.ansible_user} ansible_host=%s ip=%s etcd_member_name=etcd%d",
      keys(module.kubernetes.master_ip),
      values(module.kubernetes.master_ip),
      values(module.kubernetes.master_ip),
    range(1, length(module.kubernetes.master_ip) + 1))),
    connection_strings_worker = join("\n", formatlist("%s ansible_user=${var.ansible_user} ansible_host=%s ip=%s",
      keys(module.kubernetes.worker_ip),
      values(module.kubernetes.worker_ip),
    values(module.kubernetes.worker_ip))),
    list_master = join("\n", keys(module.kubernetes.master_ip)),
    list_worker = join("\n", keys(module.kubernetes.worker_ip))
  })
  filename = var.inventory_file
}
