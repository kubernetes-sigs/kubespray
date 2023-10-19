variable "AWS_ACCESS_KEY_ID" {
  description = "AWS Access Key"
}

variable "AWS_SECRET_ACCESS_KEY" {
  description = "AWS Secret Key"
}

variable "AWS_SSH_KEY_NAME" {
  description = "Name of the SSH keypair to use in AWS."
}

variable "AWS_DEFAULT_REGION" {
  description = "AWS Region"
}

//General Cluster Settings

variable "aws_cluster_name" {
  description = "Name of AWS Cluster"
}

variable "ami_name_pattern" {
  description = "The name pattern to use for AMI lookup"
  type        = string
  default     = "debian-10-amd64-*"
}

variable "ami_virtualization_type" {
  description = "The virtualization type to use for AMI lookup"
  type        = string
  default     = "hvm"
}

variable "ami_owners" {
  description = "The owners to use for AMI lookup"
  type        = list(string)
  default     = ["136693071363"]
}

data "aws_ami" "distro" {
  most_recent = true

  filter {
    name   = "name"
    values = [var.ami_name_pattern]
  }

  filter {
    name   = "virtualization-type"
    values = [var.ami_virtualization_type]
  }

  owners = var.ami_owners
}

//AWS VPC Variables

variable "aws_vpc_cidr_block" {
  description = "CIDR Block for VPC"
}

variable "aws_cidr_subnets_private" {
  description = "CIDR Blocks for private subnets in Availability Zones"
  type        = list(string)
}

variable "aws_cidr_subnets_public" {
  description = "CIDR Blocks for public subnets in Availability Zones"
  type        = list(string)
}

//AWS EC2 Settings

variable "aws_bastion_size" {
  description = "EC2 Instance Size of Bastion Host"
}

/*
* AWS EC2 Settings
* The number should be divisable by the number of used
* AWS Availability Zones without an remainder.
*/
variable "aws_bastion_num" {
  description = "Number of Bastion Nodes"
}

variable "aws_kube_master_num" {
  description = "Number of Kubernetes Master Nodes"
}

variable "aws_kube_master_disk_size" {
  description = "Disk size for Kubernetes Master Nodes (in GiB)"
}

variable "aws_kube_master_size" {
  description = "Instance size of Kube Master Nodes"
}

variable "aws_etcd_num" {
  description = "Number of etcd Nodes"
}

variable "aws_etcd_disk_size" {
  description = "Disk size for etcd Nodes (in GiB)"
}

variable "aws_etcd_size" {
  description = "Instance size of etcd Nodes"
}

variable "aws_kube_worker_num" {
  description = "Number of Kubernetes Worker Nodes"
}

variable "aws_kube_worker_disk_size" {
  description = "Disk size for Kubernetes Worker Nodes (in GiB)"
}

variable "aws_kube_worker_size" {
  description = "Instance size of Kubernetes Worker Nodes"
}

/*
* AWS NLB Settings
*
*/
variable "aws_nlb_api_port" {
  description = "Port for AWS NLB"
}

variable "k8s_secure_api_port" {
  description = "Secure Port of K8S API Server"
}

variable "default_tags" {
  description = "Default tags for all resources"
  type        = map(string)
}

variable "inventory_file" {
  description = "Where to store the generated inventory file"
}
