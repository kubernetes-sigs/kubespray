resource "vsphere_virtual_machine" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  name                = each.key
  resource_pool_id    = var.pool_id
  datastore_id        = var.datastore_id

  num_cpus            = var.worker_cores
  memory              = var.worker_memory
  memory_reservation  = var.worker_memory
  guest_id            = var.guest_id
  enable_disk_uuid    = "true"
  scsi_type           = var.scsi_type
  folder              = var.folder
  firmware            = var.firmware
  hardware_version    = var.hardware_version

  wait_for_guest_net_routable = false

  network_interface {
    network_id        = var.network_id
    adapter_type      = var.adapter_type
  }

  disk {
    label             = "disk0"
    size              = var.worker_disk_size
    thin_provisioned  = var.disk_thin_provisioned
  }

  lifecycle {
    ignore_changes    = [disk]
  }

  clone {
    template_uuid     = var.template_id
  }

  cdrom {
    client_device = true
  }

  vapp {
    properties = {
      "user-data" = base64encode(templatefile("${path.module}/templates/cloud-init.tmpl", { ip = each.value.ip,
                                                                  gw = var.gateway,
                                                                  dns = var.dns_primary,
                                                                  ssh_public_keys = var.ssh_public_keys}))
    }
  }
}

resource "vsphere_virtual_machine" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  name                = each.key
  resource_pool_id    = var.pool_id
  datastore_id        = var.datastore_id

  num_cpus            = var.master_cores
  memory              = var.master_memory
  memory_reservation  = var.master_memory
  guest_id            = var.guest_id
  enable_disk_uuid    = "true"
  scsi_type           = var.scsi_type
  folder              = var.folder
  firmware            = var.firmware
  hardware_version    = var.hardware_version

  network_interface {
    network_id        = var.network_id
    adapter_type      = var.adapter_type
  }

  disk {
    label             = "disk0"
    size              = var.master_disk_size
    thin_provisioned  = var.disk_thin_provisioned
  }

  lifecycle {
    ignore_changes    = [disk]
  }

  clone {
    template_uuid     = var.template_id
  }

  cdrom {
    client_device = true
  }

  vapp {
    properties = {
      "user-data" = base64encode(templatefile("${path.module}/templates/cloud-init.tmpl", { ip = each.value.ip,
                                                                  gw = var.gateway,
                                                                  dns = var.dns_primary,
                                                                  ssh_public_keys = var.ssh_public_keys}))
    }
  }
}
