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

resource "hcloud_ssh_key" "first" {
  name       = var.prefix
  public_key = var.ssh_public_keys.0
}

resource "hcloud_server" "machine" {
  for_each = {
    for name, machine in var.machines :
    name => machine
  }

  name     = "${var.prefix}-${each.key}"
  ssh_keys = [hcloud_ssh_key.first.id]
  # boot into rescue OS
  rescue = "linux64"
  # dummy value for the OS because Flatcar is not available
  image       = each.value.image
  server_type = each.value.size
  location    = var.zone
  connection {
    host        = self.ipv4_address
    timeout     = "5m"
    private_key = file(var.ssh_private_key_path)
  }
  firewall_ids = each.value.node_type == "master" ? [hcloud_firewall.master.id] : [hcloud_firewall.worker.id]
  provisioner "file" {
    content     = data.ct_config.machine-ignitions[each.key].rendered
    destination = "/root/ignition.json"
  }

  provisioner "remote-exec" {
    inline = [
      "set -ex",
      "apt update",
      "apt install -y gawk",
      "curl -fsSLO --retry-delay 1 --retry 60 --retry-connrefused --retry-max-time 60 --connect-timeout 20 https://raw.githubusercontent.com/flatcar/init/flatcar-master/bin/flatcar-install",
      "chmod +x flatcar-install",
      "./flatcar-install -s -i /root/ignition.json -C stable",
      "shutdown -r +1",
    ]
  }

  # optional:
  provisioner "remote-exec" {
    connection {
      host        = self.ipv4_address
      private_key = file(var.ssh_private_key_path)
      timeout     = "3m"
      user        = var.user_flatcar
    }

    inline = [
      "sudo hostnamectl set-hostname ${self.name}",
    ]
  }
}

resource "hcloud_server_network" "machine" {
  for_each = {
    for name, machine in var.machines :
    name => hcloud_server.machine[name]
  }
  server_id = each.value.id
  subnet_id = hcloud_network_subnet.kubernetes.id
}

data "ct_config" "machine-ignitions" {
  for_each = {
    for name, machine in var.machines :
    name => machine
  }

  strict = false
  content = templatefile(
    "${path.module}/templates/machine.yaml.tmpl",
    {
      ssh_keys     = jsonencode(var.ssh_public_keys)
      user_flatcar = var.user_flatcar
      name         = each.key
    }
  )
}

resource "hcloud_firewall" "master" {
  name = "${var.prefix}-master-firewall"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.ssh_whitelist
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "6443"
    source_ips = var.api_server_whitelist
  }
}

resource "hcloud_firewall" "worker" {
  name = "${var.prefix}-worker-firewall"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.ssh_whitelist
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = var.ingress_whitelist
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = var.ingress_whitelist
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "30000-32767"
    source_ips = var.nodeport_whitelist
  }
}
