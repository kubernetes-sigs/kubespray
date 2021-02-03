data "exoscale_compute_template" "os_image" {
  for_each = var.machines

  zone = var.zone
  name = each.value.boot_disk.image_name
}

data "exoscale_compute" "master_nodes" {
  for_each = exoscale_compute.master

  id = each.value.id

  # Since private IP address is not assigned until the nics are created we need this
  depends_on = [exoscale_nic.master_private_network_nic]
}

data "exoscale_compute" "worker_nodes" {
  for_each = exoscale_compute.worker

  id = each.value.id

  # Since private IP address is not assigned until the nics are created we need this
  depends_on = [exoscale_nic.worker_private_network_nic]
}

resource "exoscale_network" "private_network" {
  zone = var.zone
  name = "${var.prefix}-network"

  start_ip = cidrhost(var.private_network_cidr, 1)
  # cidr -1 = Broadcast address
  # cidr -2 = DHCP server address (exoscale specific)
  end_ip  = cidrhost(var.private_network_cidr, -3)
  netmask = cidrnetmask(var.private_network_cidr)
}

resource "exoscale_compute" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  display_name    = "${var.prefix}-${each.key}"
  template_id     = data.exoscale_compute_template.os_image[each.key].id
  size            = each.value.size
  disk_size       = each.value.boot_disk.root_partition_size + each.value.boot_disk.node_local_partition_size + each.value.boot_disk.ceph_partition_size
  state           = "Running"
  zone            = var.zone
  security_groups = [exoscale_security_group.master_sg.name]

  user_data = templatefile(
    "${path.module}/templates/cloud-init.tmpl",
    {
      eip_ip_address            = exoscale_ipaddress.ingress_controller_lb.ip_address
      node_local_partition_size = each.value.boot_disk.node_local_partition_size
      ceph_partition_size       = each.value.boot_disk.ceph_partition_size
      root_partition_size       = each.value.boot_disk.root_partition_size
      node_type                 = "master"
      ssh_public_keys           = var.ssh_public_keys
    }
  )
}

resource "exoscale_compute" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  display_name    = "${var.prefix}-${each.key}"
  template_id     = data.exoscale_compute_template.os_image[each.key].id
  size            = each.value.size
  disk_size       = each.value.boot_disk.root_partition_size + each.value.boot_disk.node_local_partition_size + each.value.boot_disk.ceph_partition_size
  state           = "Running"
  zone            = var.zone
  security_groups = [exoscale_security_group.worker_sg.name]

  user_data = templatefile(
    "${path.module}/templates/cloud-init.tmpl",
    {
      eip_ip_address            = exoscale_ipaddress.ingress_controller_lb.ip_address
      node_local_partition_size = each.value.boot_disk.node_local_partition_size
      ceph_partition_size       = each.value.boot_disk.ceph_partition_size
      root_partition_size       = each.value.boot_disk.root_partition_size
      node_type                 = "worker"
      ssh_public_keys           = var.ssh_public_keys
    }
  )
}

resource "exoscale_nic" "master_private_network_nic" {
  for_each = exoscale_compute.master

  compute_id = each.value.id
  network_id = exoscale_network.private_network.id
}

resource "exoscale_nic" "worker_private_network_nic" {
  for_each = exoscale_compute.worker

  compute_id = each.value.id
  network_id = exoscale_network.private_network.id
}

resource "exoscale_security_group" "master_sg" {
  name        = "${var.prefix}-master-sg"
  description = "Security group for Kubernetes masters"
}

resource "exoscale_security_group_rules" "master_sg_rules" {
  security_group_id = exoscale_security_group.master_sg.id

  # SSH
  ingress {
    protocol  = "TCP"
    cidr_list = var.ssh_whitelist
    ports     = ["22"]
  }

  # Kubernetes API
  ingress {
    protocol  = "TCP"
    cidr_list = var.api_server_whitelist
    ports     = ["6443"]
  }
}

resource "exoscale_security_group" "worker_sg" {
  name        = "${var.prefix}-worker-sg"
  description = "security group for kubernetes worker nodes"
}

resource "exoscale_security_group_rules" "worker_sg_rules" {
  security_group_id = exoscale_security_group.worker_sg.id

  # SSH
  ingress {
    protocol  = "TCP"
    cidr_list = var.ssh_whitelist
    ports     = ["22"]
  }

  # HTTP(S)
  ingress {
    protocol  = "TCP"
    cidr_list = ["0.0.0.0/0"]
    ports     = ["80", "443"]
  }

  # Kubernetes Nodeport
  ingress {
    protocol  = "TCP"
    cidr_list = var.nodeport_whitelist
    ports     = ["30000-32767"]
  }
}

resource "exoscale_ipaddress" "ingress_controller_lb" {
  zone                     = var.zone
  healthcheck_mode         = "http"
  healthcheck_port         = 80
  healthcheck_path         = "/healthz"
  healthcheck_interval     = 10
  healthcheck_timeout      = 2
  healthcheck_strikes_ok   = 2
  healthcheck_strikes_fail = 3
}

resource "exoscale_secondary_ipaddress" "ingress_controller_lb" {
  for_each = exoscale_compute.worker

  compute_id = each.value.id
  ip_address = exoscale_ipaddress.ingress_controller_lb.ip_address
}

resource "exoscale_ipaddress" "control_plane_lb" {
  zone                     = var.zone
  healthcheck_mode         = "tcp"
  healthcheck_port         = 6443
  healthcheck_interval     = 10
  healthcheck_timeout      = 2
  healthcheck_strikes_ok   = 2
  healthcheck_strikes_fail = 3
}

resource "exoscale_secondary_ipaddress" "control_plane_lb" {
  for_each = exoscale_compute.master

  compute_id = each.value.id
  ip_address = exoscale_ipaddress.control_plane_lb.ip_address
}
