data "exoscale_template" "os_image" {
  for_each = var.machines

  zone = var.zone
  name = each.value.boot_disk.image_name
}

data "exoscale_compute_instance" "master_nodes" {
  for_each = exoscale_compute_instance.master

  id   = each.value.id
  zone = var.zone
}

data "exoscale_compute_instance" "worker_nodes" {
  for_each = exoscale_compute_instance.worker

  id   = each.value.id
  zone = var.zone
}

resource "exoscale_private_network" "private_network" {
  zone = var.zone
  name = "${var.prefix}-network"

  start_ip = cidrhost(var.private_network_cidr, 1)
  # cidr -1 = Broadcast address
  # cidr -2 = DHCP server address (exoscale specific)
  end_ip  = cidrhost(var.private_network_cidr, -3)
  netmask = cidrnetmask(var.private_network_cidr)
}

resource "exoscale_compute_instance" "master" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "master"
  }

  name               = "${var.prefix}-${each.key}"
  template_id        = data.exoscale_template.os_image[each.key].id
  type               = each.value.size
  disk_size          = each.value.boot_disk.root_partition_size + each.value.boot_disk.node_local_partition_size + each.value.boot_disk.ceph_partition_size
  state              = "Running"
  zone               = var.zone
  security_group_ids = [exoscale_security_group.master_sg.id]
  network_interface {
    network_id = exoscale_private_network.private_network.id
  }
  elastic_ip_ids = [exoscale_elastic_ip.control_plane_lb.id]

  user_data = templatefile(
    "${path.module}/templates/cloud-init.tmpl",
    {
      eip_ip_address            = exoscale_elastic_ip.ingress_controller_lb.ip_address
      node_local_partition_size = each.value.boot_disk.node_local_partition_size
      ceph_partition_size       = each.value.boot_disk.ceph_partition_size
      root_partition_size       = each.value.boot_disk.root_partition_size
      node_type                 = "master"
      ssh_public_keys           = var.ssh_public_keys
    }
  )
}

resource "exoscale_compute_instance" "worker" {
  for_each = {
    for name, machine in var.machines :
    name => machine
    if machine.node_type == "worker"
  }

  name               = "${var.prefix}-${each.key}"
  template_id        = data.exoscale_template.os_image[each.key].id
  type               = each.value.size
  disk_size          = each.value.boot_disk.root_partition_size + each.value.boot_disk.node_local_partition_size + each.value.boot_disk.ceph_partition_size
  state              = "Running"
  zone               = var.zone
  security_group_ids = [exoscale_security_group.worker_sg.id]
  network_interface {
    network_id = exoscale_private_network.private_network.id
  }
  elastic_ip_ids = [exoscale_elastic_ip.ingress_controller_lb.id]

  user_data = templatefile(
    "${path.module}/templates/cloud-init.tmpl",
    {
      eip_ip_address            = exoscale_elastic_ip.ingress_controller_lb.ip_address
      node_local_partition_size = each.value.boot_disk.node_local_partition_size
      ceph_partition_size       = each.value.boot_disk.ceph_partition_size
      root_partition_size       = each.value.boot_disk.root_partition_size
      node_type                 = "worker"
      ssh_public_keys           = var.ssh_public_keys
    }
  )
}

resource "exoscale_security_group" "master_sg" {
  name        = "${var.prefix}-master-sg"
  description = "Security group for Kubernetes masters"
}

resource "exoscale_security_group_rule" "master_sg_rule_ssh" {
  security_group_id = exoscale_security_group.master_sg.id

  for_each = toset(var.ssh_whitelist)
  # SSH
  type       = "INGRESS"
  start_port = 22
  end_port   = 22
  protocol   = "TCP"
  cidr       = each.value
}

resource "exoscale_security_group_rule" "master_sg_rule_k8s_api" {
  security_group_id = exoscale_security_group.master_sg.id

  for_each = toset(var.api_server_whitelist)
  # Kubernetes API
  type       = "INGRESS"
  start_port = 6443
  end_port   = 6443
  protocol   = "TCP"
  cidr       = each.value
}

resource "exoscale_security_group" "worker_sg" {
  name        = "${var.prefix}-worker-sg"
  description = "security group for kubernetes worker nodes"
}

resource "exoscale_security_group_rule" "worker_sg_rule_ssh" {
  security_group_id = exoscale_security_group.worker_sg.id

  # SSH
  for_each   = toset(var.ssh_whitelist)
  type       = "INGRESS"
  start_port = 22
  end_port   = 22
  protocol   = "TCP"
  cidr       = each.value
}

resource "exoscale_security_group_rule" "worker_sg_rule_http" {
  security_group_id = exoscale_security_group.worker_sg.id

  # HTTP(S)
  for_each   = toset(["80", "443"])
  type       = "INGRESS"
  start_port = each.value
  end_port   = each.value
  protocol   = "TCP"
  cidr       = "0.0.0.0/0"
}


resource "exoscale_security_group_rule" "worker_sg_rule_nodeport" {
  security_group_id = exoscale_security_group.worker_sg.id

  # HTTP(S)
  for_each   = toset(var.nodeport_whitelist)
  type       = "INGRESS"
  start_port = 30000
  end_port   = 32767
  protocol   = "TCP"
  cidr       = each.value
}

resource "exoscale_elastic_ip" "ingress_controller_lb" {
  zone = var.zone
  healthcheck {
    mode         = "http"
    port         = 80
    uri          = "/healthz"
    interval     = 10
    timeout      = 2
    strikes_ok   = 2
    strikes_fail = 3
  }
}

resource "exoscale_elastic_ip" "control_plane_lb" {
  zone = var.zone
  healthcheck {
    mode         = "tcp"
    port         = 6443
    interval     = 10
    timeout      = 2
    strikes_ok   = 2
    strikes_fail = 3
  }
}
