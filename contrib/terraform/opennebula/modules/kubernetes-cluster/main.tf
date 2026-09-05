locals {
  masters = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }
  workers = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }
  context = {
    NETWORK        = "YES"
    SET_HOSTNAME   = "$NAME"
    SSH_PUBLIC_KEY = join("\n", var.ssh_public_keys)
  }
  node_network_id = var.network_reservation_size > 0 ? opennebula_virtual_network.reservation[0].id : var.network_id
}

# Optional reservation carved out of the parent network (one AR only —
# provider issue #625)
resource "opennebula_virtual_network" "reservation" {
  count                = var.network_reservation_size > 0 ? 1 : 0
  name                 = "${var.prefix}-reservation"
  reservation_vnet     = var.network_id
  reservation_size     = var.network_reservation_size
  reservation_first_ip = var.network_reservation_first_ip != "" ? var.network_reservation_first_ip : null
  reservation_ar_id    = var.network_reservation_ar_id

  lifecycle {
    precondition {
      condition     = var.network_reservation_size >= length(var.machines)
      error_message = "network_reservation_size must be at least the number of machines (each node leases one address from the reservation)."
    }
  }
}

# Optional shared non-persistent DATABLOCK image; every VM attaching it gets
# its own clone, deleted together with the VM
data "opennebula_datastore" "image" {
  count = var.additional_disk_size > 0 ? 1 : 0
  name  = var.image_datastore_name

  lifecycle {
    precondition {
      condition     = var.image_datastore_name != ""
      error_message = "image_datastore_name must be set when additional_disk_size > 0."
    }
  }
}

resource "opennebula_image" "extra_disk" {
  count        = var.additional_disk_size > 0 ? 1 : 0
  name         = "${var.prefix}-extra-disk"
  datastore_id = data.opennebula_datastore.image[0].id
  type         = "DATABLOCK"
  size         = var.additional_disk_size
  persistent   = false
  permissions  = "600"
}

# Anti-affinity: spread control-plane VMs across hosts
resource "opennebula_virtual_machine_group" "cluster" {
  count = var.masters_anti_affinity ? 1 : 0
  name  = "${var.prefix}-vm-group"

  role {
    name   = "master"
    policy = "ANTI_AFFINED"
  }
}

resource "opennebula_virtual_machine" "master" {
  for_each = local.masters

  name        = "${var.prefix}-${each.key}"
  template_id = var.template_id
  cpu         = var.master_cpu
  vcpu        = var.master_vcpu
  memory      = var.master_memory

  context = local.context

  nic {
    model      = "virtio"
    network_id = local.node_network_id
    ip         = each.value.ip != "" ? each.value.ip : null
  }

  # Any disk block replaces ALL of the template's disks (provider merge
  # semantics), so the OS disk must be re-declared whenever another disk
  # block is emitted.
  dynamic "disk" {
    for_each = var.master_disk_size > 0 || var.additional_disk_size > 0 ? [1] : []
    content {
      image_id = var.template_disk_image_id
      size     = var.master_disk_size > 0 ? var.master_disk_size : (var.template_disk_size > 0 ? var.template_disk_size : null)
    }
  }

  dynamic "disk" {
    for_each = var.additional_disk_size > 0 ? [1] : []
    content {
      image_id = opennebula_image.extra_disk[0].id
    }
  }

  dynamic "vmgroup" {
    for_each = var.masters_anti_affinity ? [1] : []
    content {
      vmgroup_id = opennebula_virtual_machine_group.cluster[0].id
      role       = "master"
    }
  }

  timeouts {
    create = var.vm_create_timeout
  }

  lifecycle {
    precondition {
      condition     = (var.master_disk_size <= 0 && var.additional_disk_size <= 0) || var.template_disk_image_id != null
      error_message = "master_disk_size/additional_disk_size require the template's first disk to reference its image by numeric IMAGE_ID (templates referencing the image by name are not readable through the provider data source)."
    }
  }
}

resource "opennebula_virtual_machine" "worker" {
  for_each = local.workers

  name        = "${var.prefix}-${each.key}"
  template_id = var.template_id
  cpu         = var.worker_cpu
  vcpu        = var.worker_vcpu
  memory      = var.worker_memory

  context = local.context

  nic {
    model      = "virtio"
    network_id = local.node_network_id
    ip         = each.value.ip != "" ? each.value.ip : null
  }

  # Any disk block replaces ALL of the template's disks (provider merge
  # semantics), so the OS disk must be re-declared whenever another disk
  # block is emitted.
  dynamic "disk" {
    for_each = var.worker_disk_size > 0 || var.additional_disk_size > 0 ? [1] : []
    content {
      image_id = var.template_disk_image_id
      size     = var.worker_disk_size > 0 ? var.worker_disk_size : (var.template_disk_size > 0 ? var.template_disk_size : null)
    }
  }

  dynamic "disk" {
    for_each = var.additional_disk_size > 0 ? [1] : []
    content {
      image_id = opennebula_image.extra_disk[0].id
    }
  }

  timeouts {
    create = var.vm_create_timeout
  }

  lifecycle {
    precondition {
      condition     = (var.worker_disk_size <= 0 && var.additional_disk_size <= 0) || var.template_disk_image_id != null
      error_message = "worker_disk_size/additional_disk_size require the template's first disk to reference its image by numeric IMAGE_ID (templates referencing the image by name are not readable through the provider data source)."
    }
  }
}
