resource "hcloud_network" "kubernetes" {
  name     = "${var.prefix}-network"
  ip_range = var.private_network_cidr
}

resource "hcloud_network_subnet" "kubernetes" {
  type         = "cloud"
  network_id   = hcloud_network.kubernetes.id
  network_zone = var.network_zone
  ip_range     = var.private_subnet_cidr
}

resource "hcloud_server" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  name        = "${var.prefix}-${each.key}"
  image       = each.value.image
  server_type = each.value.size
  location    = var.zone

  user_data = templatefile(
    "${path.module}/templates/cloud-init.tmpl",
    {
      ssh_public_keys = var.ssh_public_keys
    }
  )

  firewall_ids = [hcloud_firewall.master.id]
}

resource "hcloud_server_network" "master" {
  for_each = hcloud_server.master

  server_id = each.value.id

  subnet_id = hcloud_network_subnet.kubernetes.id
}

resource "hcloud_server" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  name        = "${var.prefix}-${each.key}"
  image       = each.value.image
  server_type = each.value.size
  location    = var.zone

  user_data = templatefile(
    "${path.module}/templates/cloud-init.tmpl",
    {
      ssh_public_keys = var.ssh_public_keys
    }
  )

  firewall_ids = [hcloud_firewall.worker.id]

}

resource "hcloud_server_network" "worker" {
  for_each = hcloud_server.worker

  server_id = each.value.id

  subnet_id = hcloud_network_subnet.kubernetes.id
}

resource "hcloud_firewall" "master" {
  name = "${var.prefix}-master-firewall"

  rule {
   direction = "in"
   protocol = "tcp"
   port = "22"
   source_ips = var.ssh_whitelist
  }

  rule {
   direction = "in"
   protocol = "tcp"
   port = "6443"
   source_ips = var.api_server_whitelist
  }
}

resource "hcloud_firewall" "worker" {
  name = "${var.prefix}-worker-firewall"

  rule {
   direction = "in"
   protocol = "tcp"
   port = "22"
   source_ips = var.ssh_whitelist
  }

  rule {
   direction = "in"
   protocol = "tcp"
   port = "80"
   source_ips = var.ingress_whitelist
  }

  rule {
   direction = "in"
   protocol = "tcp"
   port = "443"
   source_ips = var.ingress_whitelist
  }

  rule {
   direction = "in"
   protocol = "tcp"
   port = "30000-32767"
   source_ips = var.nodeport_whitelist
  }
}
