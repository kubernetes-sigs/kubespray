locals {
  # Create a list of all disks to create
  disks = flatten([
    for node_name, machine in var.machines : [
      for disk_name, disk in machine.additional_disks : {
        disk = disk
        disk_name = disk_name
        node_name = node_name
      }
    ]
  ])

  # If prefix is set, all resources will be prefixed with "${var.prefix}-"
  # Else don't prefix with anything
  resource-prefix = "%{ if var.prefix != ""}${var.prefix}-%{ endif }"
}

resource "upcloud_network" "private" {
  name = "${local.resource-prefix}k8s-network"
  zone = var.zone

  ip_network {
    address = var.private_network_cidr
    dhcp    = true
    family  = "IPv4"
  }
}

resource "upcloud_storage" "additional_disks" {
  for_each = {
    for disk in local.disks: "${disk.node_name}_${disk.disk_name}" => disk.disk
  }

  size  = each.value.size
  tier  = each.value.tier
  title = "${local.resource-prefix}${each.key}"
  zone  = var.zone
}

resource "upcloud_server" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  hostname = "${local.resource-prefix}${each.key}"
  cpu      = each.value.cpu
  mem      = each.value.mem
  zone     = var.zone

  template {
  storage = var.template_name
  size    = each.value.disk_size
  }

  # Public network interface
  network_interface {
    type = "public"
  }

  # Private network interface
  network_interface {
    type    = "private"
    network = upcloud_network.private.id
  }

  dynamic "storage_devices" {
    for_each = {
      for disk_key_name, disk in upcloud_storage.additional_disks :
        disk_key_name => disk
        # Only add the disk if it matches the node name in the start of its name
        if length(regexall("^${each.key}_.+", disk_key_name)) > 0
    }

    content {
      storage = storage_devices.value.id
    }
  }

  # Include at least one public SSH key
  login {
    user            = var.username
    keys            = var.ssh_public_keys
    create_password = false
  }
}

resource "upcloud_server" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  hostname = "${local.resource-prefix}${each.key}"
  cpu      = each.value.cpu
  mem      = each.value.mem
  zone     = var.zone

  template {
    storage = var.template_name
    size    = each.value.disk_size
  }

  # Public network interface
  network_interface {
    type = "public"
  }

  # Private network interface
  network_interface {
    type    = "private"
    network = upcloud_network.private.id
  }

  dynamic "storage_devices" {
    for_each = {
      for disk_key_name, disk in upcloud_storage.additional_disks :
        disk_key_name => disk
        # Only add the disk if it matches the node name in the start of its name
        if length(regexall("^${each.key}_.+", disk_key_name)) > 0
    }

    content {
      storage = storage_devices.value.id
    }
  }

  # Include at least one public SSH key
  login {
    user            = var.username
    keys            = var.ssh_public_keys
    create_password = false
  }
}
