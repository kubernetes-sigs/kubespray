terraform {
  required_version = ">= 0.12.0"
}

provider "aws" {
  access_key = var.AWS_ACCESS_KEY_ID
  secret_key = var.AWS_SECRET_ACCESS_KEY
  region     = var.AWS_DEFAULT_REGION
}

data "aws_availability_zones" "available" {}

/*
* Calling modules who create the initial AWS VPC / AWS ELB
* and AWS IAM Roles for Kubernetes Deployment
*/

module "aws-vpc" {
  source = "./modules/vpc"

  aws_cluster_name         = var.aws_cluster_name
  aws_vpc_cidr_block       = var.aws_vpc_cidr_block
  aws_avail_zones          = data.aws_availability_zones.available.names
  aws_cidr_subnets_private = var.aws_cidr_subnets_private
  aws_cidr_subnets_public  = var.aws_cidr_subnets_public
  default_tags             = var.default_tags
}

module "aws-nlb" {
  source = "./modules/nlb"

  aws_cluster_name     = var.aws_cluster_name
  aws_vpc_id           = module.aws-vpc.aws_vpc_id
  aws_avail_zones      = data.aws_availability_zones.available.names
  aws_elb_api_subnets  = var.aws_elb_api_public_subnet? module.aws-vpc.aws_subnet_ids_public : module.aws-vpc.aws_subnet_ids_private
  aws_elb_api_internal = var.aws_elb_api_internal
  aws_elb_api_port     = var.aws_elb_api_port
  k8s_secure_api_port  = var.k8s_secure_api_port
  default_tags         = var.default_tags
}

module "aws-iam" {
  source = "./modules/iam"

  aws_cluster_name = var.aws_cluster_name
}

/*
* Create Bastion Instances in AWS
*
*/

resource "aws_instance" "bastion-server" {
  ami                         = data.aws_ami.distro.id
  instance_type               = var.aws_bastion_size
  count                       = var.aws_bastion_num
  associate_public_ip_address = true
  subnet_id                   = element(module.aws-vpc.aws_subnet_ids_public, count.index)

  vpc_security_group_ids = module.aws-vpc.aws_security_group

  key_name = var.AWS_SSH_KEY_NAME

  tags = merge(var.default_tags, tomap({
    Name    = "kubernetes-${var.aws_cluster_name}-bastion-${count.index}"
    Cluster = var.aws_cluster_name
    Role    = "bastion-${var.aws_cluster_name}-${count.index}"
  }))
}

/*
* Create K8s Master and worker nodes and etcd instances
*
*/

resource "aws_instance" "k8s-master" {
  ami           = data.aws_ami.distro.id
  instance_type = var.aws_kube_master_size

  count = var.aws_kube_master_num

  source_dest_check     = var.aws_src_dest_check
  subnet_id         = element(module.aws-vpc.aws_subnet_ids_private, count.index)

  vpc_security_group_ids = module.aws-vpc.aws_security_group

  iam_instance_profile = module.aws-iam.kube_control_plane-profile
  key_name             = var.AWS_SSH_KEY_NAME

  tags = merge(var.default_tags, tomap({
    Name                                            = "kubernetes-${var.aws_cluster_name}-master${count.index}"
    "kubernetes.io/cluster/${var.aws_cluster_name}" = "member"
    Role                                            = "master"
  }))
}

resource "aws_lb_target_group_attachment" "tg-attach_master_nodes" {
  count    = var.aws_kube_master_num
  target_group_arn = module.aws-nlb.aws_nlb_api_tg_arn
  target_id = element(aws_instance.k8s-master.*.private_ip, count.index)
}

resource "aws_instance" "k8s-etcd" {
  ami           = data.aws_ami.distro.id
  instance_type = var.aws_etcd_size

  count = var.aws_etcd_num

  source_dest_check     = var.aws_src_dest_check
  subnet_id         = element(module.aws-vpc.aws_subnet_ids_private, count.index)

  vpc_security_group_ids = module.aws-vpc.aws_security_group

  key_name = var.AWS_SSH_KEY_NAME

  tags = merge(var.default_tags, tomap({
    Name                                            = "kubernetes-${var.aws_cluster_name}-etcd${count.index}"
    "kubernetes.io/cluster/${var.aws_cluster_name}" = "member"
    Role                                            = "etcd"
  }))
}

resource "aws_instance" "k8s-worker" {
  ami           = data.aws_ami.distro.id
  instance_type = var.aws_kube_worker_size

  count = var.aws_kube_worker_num

  source_dest_check     = var.aws_src_dest_check
  subnet_id         = element(module.aws-vpc.aws_subnet_ids_private, count.index)

  vpc_security_group_ids = module.aws-vpc.aws_security_group

  iam_instance_profile = module.aws-iam.kube-worker-profile
  key_name             = var.AWS_SSH_KEY_NAME

  tags = merge(var.default_tags, tomap({
    Name                                            = "kubernetes-${var.aws_cluster_name}-worker${count.index}"
    "kubernetes.io/cluster/${var.aws_cluster_name}" = "member"
    Role                                            = "worker"
  }))
}

/*
* Create EFS file system and mount target
*
*/

resource "aws_efs_file_system" "efs" {
  encrypted = "true"
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
  lifecycle_policy {
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  tags = {
    Name = "kubernetes-${var.aws_cluster_name}-efs"
  }
}

resource "aws_efs_backup_policy" "policy" {
  file_system_id = aws_efs_file_system.efs.id

  backup_policy {
    status = "ENABLED"
  }
}

resource "aws_efs_mount_target" "alpha" {
  count = length(var.aws_cidr_subnets_public) > length(data.aws_availability_zones.available.names) ? length(data.aws_availability_zones.available.names) : length(var.aws_cidr_subnets_public)

  file_system_id = aws_efs_file_system.efs.id
  subnet_id = element(module.aws-vpc.aws_subnet_ids_public, count.index)
}

/*
* Add inbound rule to the default security group used by efs
*
*/

data "aws_security_group" "default" {
  name = "default"
  vpc_id = module.aws-vpc.aws_vpc_id
}

resource "aws_security_group_rule" "allow-all-ingress" {
  type = "ingress"
  from_port = 0
  to_port = 65535
  protocol = "-1"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = data.aws_security_group.default.id
}

/*
* Create Kubespray Inventory File
*
*/
data "template_file" "inventory" {
  template = file("${path.module}/templates/inventory.tpl")

  vars = {
    public_ip_address_bastion = join("\n", formatlist("bastion ansible_host=%s", aws_instance.bastion-server.*.public_ip))
    connection_strings_master = join("\n", formatlist("%s ansible_host=%s", aws_instance.k8s-master.*.private_dns, aws_instance.k8s-master.*.private_ip))
    connection_strings_node   = join("\n", formatlist("%s ansible_host=%s", aws_instance.k8s-worker.*.private_dns, aws_instance.k8s-worker.*.private_ip))
    connection_strings_etcd   = join("\n", formatlist("%s ansible_host=%s", aws_instance.k8s-etcd.*.private_dns, aws_instance.k8s-etcd.*.private_ip))
    list_master               = join("\n", aws_instance.k8s-master.*.private_dns)
    list_node                 = join("\n", aws_instance.k8s-worker.*.private_dns)
    list_etcd                 = join("\n", aws_instance.k8s-etcd.*.private_dns)
    nlb_api_fqdn              = "apiserver_loadbalancer_domain_name=\"${module.aws-nlb.aws_nlb_api_fqdn}\""
    aws_efs_filesystem        = "aws_efs_filesystem_id=${aws_efs_file_system.efs.id}"
  }
}

resource "null_resource" "inventories" {
  provisioner "local-exec" {
    command = "echo '${data.template_file.inventory.rendered}' > ${var.inventory_file}"
  }

  triggers = {
    template = data.template_file.inventory.rendered
  }
}

/*
* Create Transit Gateway
*
*/
module "transit_gateway" {
  source = "./modules/tgw"

  count = var.vpn_connection_enable ? 1 : 0

  create_tgw       = var.vpn_connection_enable
  
  aws_cluster_name = var.aws_cluster_name

  vpc_attachments  = {
    vpc = {
      vpc_id       = module.aws-vpc.aws_vpc_id
      subnet_ids   = module.aws-vpc.aws_subnet_ids_private

      tgw_routes   = flatten([
        for cidr in var.aws_cidr_subnets_private: {
          destination_cidr_block = cidr
        }
      ])
    }
  }

  default_tags = var.default_tags
}

/*
* VPN Connection
*
*/
module "vpn_connection" {
  source = "./modules/vpn"

  count = var.vpn_connection_enable ? 1 : 0

  aws_cluster_name               = var.aws_cluster_name

  customer_gateway_ip_address    = var.customer_gateway_ip
  transit_gateway_id             = module.transit_gateway[0].ec2_transit_gateway_id

  local_cidr                     = var.local_cidr

  transit_gateway_route_table_id = module.transit_gateway[0].ec2_transit_gateway_route_table_id

  default_tags = var.default_tags
}

resource "aws_route" "this" {
  count = var.vpn_connection_enable ? length(module.aws-vpc.aws_route_table_private) : 0

  destination_cidr_block = var.local_cidr

  route_table_id         = element(module.aws-vpc.aws_route_table_private, count.index)
  transit_gateway_id     = module.transit_gateway[0].ec2_transit_gateway_id
}

resource "aws_security_group_rule" "allow-local-ingress" {
  count = var.vpn_connection_enable ? 1 : 0

  type              = "ingress"
  from_port         = 6443
  to_port           = 6443
  protocol          = "TCP"
  cidr_blocks       = [var.local_cidr]
  security_group_id = module.aws-vpc.aws_security_group[0]
}
