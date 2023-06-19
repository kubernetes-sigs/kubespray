provider "nifcloud" {
  region = var.region
}

module "kubernetes_cluster" {
  source = "./modules/kubernetes-cluster"

  availability_zone = var.az
  prefix            = "dev"

  private_network_cidr = var.private_network_cidr

  instance_key_name = var.instance_key_name
  instances_cp      = var.instances_cp
  instances_wk      = var.instances_wk
  image_name        = var.image_name

  instance_type_bn = var.instance_type_bn
  instance_type_cp = var.instance_type_cp
  instance_type_wk = var.instance_type_wk

  private_ip_bn = var.private_ip_bn

  additional_lb_filter = [var.working_instance_ip]
}

resource "nifcloud_security_group_rule" "ssh_from_bastion" {
  security_group_names = [
    module.kubernetes_cluster.security_group_name.bastion
  ]
  type      = "IN"
  from_port = 22
  to_port   = 22
  protocol  = "TCP"
  cidr_ip   = var.working_instance_ip
}
