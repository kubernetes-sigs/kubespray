#################################################
##
## Local variables
##
locals {
  # e.g. east-11 is 11
  az_num = reverse(split("-", var.availability_zone))[0]
  # e.g. east-11 is e11
  az_short_name = "${substr(reverse(split("-", var.availability_zone))[1], 0, 1)}${local.az_num}"

  # Port used by the protocol
  port_ssh     = 22
  port_kubectl = 6443
  port_kubelet = 10250

  # calico: https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements#network-requirements
  port_bgp   = 179
  port_vxlan = 4789
  port_etcd  = 2379
}

#################################################
##
## General
##

# data
data "nifcloud_image" "this" {
  image_name = var.image_name
}

# private lan
resource "nifcloud_private_lan" "this" {
  private_lan_name  = "${var.prefix}lan"
  availability_zone = var.availability_zone
  cidr_block        = var.private_network_cidr
  accounting_type   = var.accounting_type
}

#################################################
##
## Bastion
##
resource "nifcloud_security_group" "bn" {
  group_name        = "${var.prefix}bn"
  description       = "${var.prefix} bastion"
  availability_zone = var.availability_zone
}

resource "nifcloud_instance" "bn" {

  instance_id    = "${local.az_short_name}${var.prefix}bn01"
  security_group = nifcloud_security_group.bn.group_name
  instance_type  = var.instance_type_bn

  user_data = templatefile("${path.module}/templates/userdata.tftpl", {
    private_ip_address = var.private_ip_bn
    ssh_port           = local.port_ssh
    hostname           = "${local.az_short_name}${var.prefix}bn01"
  })

  availability_zone = var.availability_zone
  accounting_type   = var.accounting_type
  image_id          = data.nifcloud_image.this.image_id
  key_name          = var.instance_key_name

  network_interface {
    network_id = "net-COMMON_GLOBAL"
  }
  network_interface {
    network_id = nifcloud_private_lan.this.network_id
    ip_address = "static"
  }

  # The image_id changes when the OS image type is demoted from standard to public.
  lifecycle {
    ignore_changes = [
      image_id,
      user_data,
    ]
  }
}

#################################################
##
## Control Plane
##
resource "nifcloud_security_group" "cp" {
  group_name        = "${var.prefix}cp"
  description       = "${var.prefix} control plane"
  availability_zone = var.availability_zone
}

resource "nifcloud_instance" "cp" {
  for_each = var.instances_cp

  instance_id    = "${local.az_short_name}${var.prefix}${each.key}"
  security_group = nifcloud_security_group.cp.group_name
  instance_type  = var.instance_type_cp
  user_data = templatefile("${path.module}/templates/userdata.tftpl", {
    private_ip_address = each.value.private_ip
    ssh_port           = local.port_ssh
    hostname           = "${local.az_short_name}${var.prefix}${each.key}"
  })

  availability_zone = var.availability_zone
  accounting_type   = var.accounting_type
  image_id          = data.nifcloud_image.this.image_id
  key_name          = var.instance_key_name

  network_interface {
    network_id = "net-COMMON_GLOBAL"
  }
  network_interface {
    network_id = nifcloud_private_lan.this.network_id
    ip_address = "static"
  }

  # The image_id changes when the OS image type is demoted from standard to public.
  lifecycle {
    ignore_changes = [
      image_id,
      user_data,
    ]
  }
}

resource "nifcloud_load_balancer" "this" {
  load_balancer_name = "${local.az_short_name}${var.prefix}cp"
  accounting_type    = var.accounting_type
  balancing_type     = 1 // Round-Robin
  load_balancer_port = local.port_kubectl
  instance_port      = local.port_kubectl
  instances          = [for v in nifcloud_instance.cp : v.instance_id]
  filter = concat(
    [for k, v in nifcloud_instance.cp : v.public_ip],
    [for k, v in nifcloud_instance.wk : v.public_ip],
    var.additional_lb_filter,
  )
  filter_type = 1 // Allow
}

#################################################
##
## Worker
##
resource "nifcloud_security_group" "wk" {
  group_name        = "${var.prefix}wk"
  description       = "${var.prefix} worker"
  availability_zone = var.availability_zone
}

resource "nifcloud_instance" "wk" {
  for_each = var.instances_wk

  instance_id    = "${local.az_short_name}${var.prefix}${each.key}"
  security_group = nifcloud_security_group.wk.group_name
  instance_type  = var.instance_type_wk
  user_data = templatefile("${path.module}/templates/userdata.tftpl", {
    private_ip_address = each.value.private_ip
    ssh_port           = local.port_ssh
    hostname           = "${local.az_short_name}${var.prefix}${each.key}"
  })

  availability_zone = var.availability_zone
  accounting_type   = var.accounting_type
  image_id          = data.nifcloud_image.this.image_id
  key_name          = var.instance_key_name

  network_interface {
    network_id = "net-COMMON_GLOBAL"
  }
  network_interface {
    network_id = nifcloud_private_lan.this.network_id
    ip_address = "static"
  }

  # The image_id changes when the OS image type is demoted from standard to public.
  lifecycle {
    ignore_changes = [
      image_id,
      user_data,
    ]
  }
}

#################################################
##
## Security Group Rule: Kubernetes
##

# ssh
resource "nifcloud_security_group_rule" "ssh_from_bastion" {
  security_group_names = [
    nifcloud_security_group.wk.group_name,
    nifcloud_security_group.cp.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_ssh
  to_port                    = local.port_ssh
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.bn.group_name
}

# kubectl
resource "nifcloud_security_group_rule" "kubectl_from_worker" {
  security_group_names = [
    nifcloud_security_group.cp.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_kubectl
  to_port                    = local.port_kubectl
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.wk.group_name
}

# kubelet
resource "nifcloud_security_group_rule" "kubelet_from_worker" {
  security_group_names = [
    nifcloud_security_group.cp.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_kubelet
  to_port                    = local.port_kubelet
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.wk.group_name
}

resource "nifcloud_security_group_rule" "kubelet_from_control_plane" {
  security_group_names = [
    nifcloud_security_group.wk.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_kubelet
  to_port                    = local.port_kubelet
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.cp.group_name
}

#################################################
##
## Security Group Rule: calico
##

# vslan
resource "nifcloud_security_group_rule" "vxlan_from_control_plane" {
  security_group_names = [
    nifcloud_security_group.wk.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_vxlan
  to_port                    = local.port_vxlan
  protocol                   = "UDP"
  source_security_group_name = nifcloud_security_group.cp.group_name
}

resource "nifcloud_security_group_rule" "vxlan_from_worker" {
  security_group_names = [
    nifcloud_security_group.cp.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_vxlan
  to_port                    = local.port_vxlan
  protocol                   = "UDP"
  source_security_group_name = nifcloud_security_group.wk.group_name
}

# bgp
resource "nifcloud_security_group_rule" "bgp_from_control_plane" {
  security_group_names = [
    nifcloud_security_group.wk.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_bgp
  to_port                    = local.port_bgp
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.cp.group_name
}

resource "nifcloud_security_group_rule" "bgp_from_worker" {
  security_group_names = [
    nifcloud_security_group.cp.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_bgp
  to_port                    = local.port_bgp
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.wk.group_name
}

# etcd
resource "nifcloud_security_group_rule" "etcd_from_worker" {
  security_group_names = [
    nifcloud_security_group.cp.group_name,
  ]
  type                       = "IN"
  from_port                  = local.port_etcd
  to_port                    = local.port_etcd
  protocol                   = "TCP"
  source_security_group_name = nifcloud_security_group.wk.group_name
}
