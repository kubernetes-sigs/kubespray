#################################################
##
## General
##

resource "google_compute_network" "main" {
  name = "${var.prefix}-network"

  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = "${var.prefix}-subnet"
  network       = google_compute_network.main.name
  ip_cidr_range = var.private_network_cidr
  region        = var.region
}

resource "google_compute_firewall" "deny_all" {
  name    = "${var.prefix}-default-firewall"
  network = google_compute_network.main.name

  priority = 1000

  source_ranges = ["0.0.0.0/0"]

  deny {
    protocol = "all"
  }
}

resource "google_compute_firewall" "allow_internal" {
  name    = "${var.prefix}-internal-firewall"
  network = google_compute_network.main.name

  priority = 500

  source_ranges = [var.private_network_cidr]

  allow {
    protocol = "all"
  }
}

resource "google_compute_firewall" "ssh" {
  count = length(var.ssh_whitelist) > 0 ? 1 : 0

  name    = "${var.prefix}-ssh-firewall"
  network = google_compute_network.main.name

  priority = 100

  source_ranges = var.ssh_whitelist

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "api_server" {
  count = length(var.api_server_whitelist) > 0 ? 1 : 0

  name    = "${var.prefix}-api-server-firewall"
  network = google_compute_network.main.name

  priority = 100

  source_ranges = var.api_server_whitelist

  allow {
    protocol = "tcp"
    ports    = ["6443"]
  }
}

resource "google_compute_firewall" "nodeport" {
  count = length(var.nodeport_whitelist) > 0 ? 1 : 0

  name    = "${var.prefix}-nodeport-firewall"
  network = google_compute_network.main.name

  priority = 100

  source_ranges = var.nodeport_whitelist

  allow {
    protocol = "tcp"
    ports    = ["30000-32767"]
  }
}

resource "google_compute_firewall" "ingress_http" {
  count = length(var.ingress_whitelist) > 0 ? 1 : 0

  name    = "${var.prefix}-http-ingress-firewall"
  network = google_compute_network.main.name

  priority = 100

  source_ranges = var.ingress_whitelist

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
}

resource "google_compute_firewall" "ingress_https" {
  count = length(var.ingress_whitelist) > 0 ? 1 : 0

  name    = "${var.prefix}-https-ingress-firewall"
  network = google_compute_network.main.name

  priority = 100

  source_ranges = var.ingress_whitelist

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

#################################################
##
## Local variables
##

locals {
  master_target_list = [
    for name, machine in google_compute_instance.master :
    "${machine.zone}/${machine.name}"
  ]

  worker_target_list = [
    for name, machine in google_compute_instance.worker :
    "${machine.zone}/${machine.name}"
  ]

  master_disks = flatten([
    for machine_name, machine in var.machines : [
      for disk_name, disk in machine.additional_disks : {
        "${machine_name}-${disk_name}" = {
          "machine_name": machine_name,
          "machine": machine,
          "disk_size": disk.size,
          "disk_name": disk_name
        }
      }
    ]
    if machine.node_type == "master"
  ])

  worker_disks = flatten([
    for machine_name, machine in var.machines : [
      for disk_name, disk in machine.additional_disks : {
        "${machine_name}-${disk_name}" = {
          "machine_name": machine_name,
          "machine": machine,
          "disk_size": disk.size,
          "disk_name": disk_name
        }
      }
    ]
    if machine.node_type == "worker"
  ])
}

#################################################
##
## Master
##

resource "google_compute_address" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  name         = "${var.prefix}-${each.key}-pip"
  address_type = "EXTERNAL"
  region       = var.region
}

resource "google_compute_disk" "master" {
  for_each = {
    for item in local.master_disks :
     keys(item)[0] => values(item)[0]
   }

  name = "${var.prefix}-${each.key}"
  type = var.master_additional_disk_type
  zone = each.value.machine.zone
  size = each.value.disk_size

  physical_block_size_bytes = 4096
}

resource "google_compute_attached_disk" "master" {
  for_each = {
    for item in local.master_disks :
     keys(item)[0] => values(item)[0]
   }

  disk     = google_compute_disk.master[each.key].id
  instance = google_compute_instance.master[each.value.machine_name].id
}

resource "google_compute_instance" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  name         = "${var.prefix}-${each.key}"
  machine_type = each.value.size
  zone         = each.value.zone

  tags = ["control-plane", "master", each.key]

  boot_disk {
    initialize_params {
      image = each.value.boot_disk.image_name
      size = each.value.boot_disk.size
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.name

    access_config {
      nat_ip = google_compute_address.master[each.key].address
    }
  }

  metadata = {
    ssh-keys = "ubuntu:${trimspace(file(pathexpand(var.ssh_pub_key)))}"
  }

  service_account {
    email  = var.master_sa_email
    scopes = var.master_sa_scopes
  }

  # Since we use google_compute_attached_disk we need to ignore this
  lifecycle {
    ignore_changes = [attached_disk]
  }

  scheduling {
    preemptible = var.master_preemptible
    automatic_restart = !var.master_preemptible
  }
}

resource "google_compute_forwarding_rule" "master_lb" {
  count = length(var.api_server_whitelist) > 0 ? 1 : 0

  name = "${var.prefix}-master-lb-forward-rule"

  port_range = "6443"

  target = google_compute_target_pool.master_lb[count.index].id
}

resource "google_compute_target_pool" "master_lb" {
  count = length(var.api_server_whitelist) > 0 ? 1 : 0

  name      = "${var.prefix}-master-lb-pool"
  instances = local.master_target_list
}

#################################################
##
## Worker
##

resource "google_compute_disk" "worker" {
  for_each = {
    for item in local.worker_disks :
     keys(item)[0] => values(item)[0]
   }

  name = "${var.prefix}-${each.key}"
  type = var.worker_additional_disk_type
  zone = each.value.machine.zone
  size = each.value.disk_size

  physical_block_size_bytes = 4096
}

resource "google_compute_attached_disk" "worker" {
  for_each = {
    for item in local.worker_disks :
     keys(item)[0] => values(item)[0]
   }

  disk     = google_compute_disk.worker[each.key].id
  instance = google_compute_instance.worker[each.value.machine_name].id
}

resource "google_compute_address" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  name         = "${var.prefix}-${each.key}-pip"
  address_type = "EXTERNAL"
  region       = var.region
}

resource "google_compute_instance" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  name         = "${var.prefix}-${each.key}"
  machine_type = each.value.size
  zone         = each.value.zone

  tags = ["worker", each.key]

  boot_disk {
    initialize_params {
      image = each.value.boot_disk.image_name
      size = each.value.boot_disk.size
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.name

    access_config {
      nat_ip = google_compute_address.worker[each.key].address
    }
  }

  metadata = {
    ssh-keys = "ubuntu:${trimspace(file(pathexpand(var.ssh_pub_key)))}"
  }

  service_account {
    email  = var.worker_sa_email
    scopes = var.worker_sa_scopes
  }

  # Since we use google_compute_attached_disk we need to ignore this
  lifecycle {
    ignore_changes = [attached_disk]
  }

  scheduling {
    preemptible = var.worker_preemptible
    automatic_restart = !var.worker_preemptible
  }
}

resource "google_compute_address" "worker_lb" {
  count = length(var.ingress_whitelist) > 0 ? 1 : 0

  name         = "${var.prefix}-worker-lb-address"
  address_type = "EXTERNAL"
  region       = var.region
}

resource "google_compute_forwarding_rule" "worker_http_lb" {
  count = length(var.ingress_whitelist) > 0 ? 1 : 0

  name = "${var.prefix}-worker-http-lb-forward-rule"

  ip_address = google_compute_address.worker_lb[count.index].address
  port_range = "80"

  target = google_compute_target_pool.worker_lb[count.index].id
}

resource "google_compute_forwarding_rule" "worker_https_lb" {
  count = length(var.ingress_whitelist) > 0 ? 1 : 0

  name = "${var.prefix}-worker-https-lb-forward-rule"

  ip_address = google_compute_address.worker_lb[count.index].address
  port_range = "443"

  target = google_compute_target_pool.worker_lb[count.index].id
}

resource "google_compute_target_pool" "worker_lb" {
  count = length(var.ingress_whitelist) > 0 ? 1 : 0

  name      = "${var.prefix}-worker-lb-pool"
  instances = local.worker_target_list
}

resource "google_compute_firewall" "extra_ingress_firewall" {
  for_each = {
    for name, firewall in var.extra_ingress_firewalls :
    name => firewall
  }

  name    = "${var.prefix}-${each.key}-ingress"
  network = google_compute_network.main.name

  priority = 100

  source_ranges = each.value.source_ranges

  target_tags = each.value.target_tags

  allow {
    protocol = each.value.protocol
    ports    = each.value.ports
  }
}
