#################################################
##
## General
##

resource "google_compute_network" "main" {
  name = "${var.prefix}-network"
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
  name    = "${var.prefix}-http-ingress-firewall"
  network = google_compute_network.main.name

  priority = 100

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
}

resource "google_compute_firewall" "ingress_https" {
  name    = "${var.prefix}-https-ingress-firewall"
  network = google_compute_network.main.name

  priority = 100

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
  type = "pd-ssd"
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

  tags = ["master"]

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
    ignore_changes = ["attached_disk"]
  }
}

resource "google_compute_forwarding_rule" "master_lb" {
  name = "${var.prefix}-master-lb-forward-rule"

  port_range = "6443"

  target = google_compute_target_pool.master_lb.id
}

resource "google_compute_target_pool" "master_lb" {
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
  type = "pd-ssd"
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

  tags = ["worker"]

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
    ignore_changes = ["attached_disk"]
  }
}

resource "google_compute_address" "worker_lb" {
  name         = "${var.prefix}-worker-lb-address"
  address_type = "EXTERNAL"
  region       = var.region
}

resource "google_compute_forwarding_rule" "worker_http_lb" {
  name = "${var.prefix}-worker-http-lb-forward-rule"

  ip_address = google_compute_address.worker_lb.address
  port_range = "80"

  target = google_compute_target_pool.worker_lb.id
}

resource "google_compute_forwarding_rule" "worker_https_lb" {
  name = "${var.prefix}-worker-https-lb-forward-rule"

  ip_address = google_compute_address.worker_lb.address
  port_range = "443"

  target = google_compute_target_pool.worker_lb.id
}

resource "google_compute_target_pool" "worker_lb" {
  name      = "${var.prefix}-worker-lb-pool"
  instances = local.worker_target_list
}
