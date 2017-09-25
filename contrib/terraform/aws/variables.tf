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


//AWS VPC Variables

variable "aws_vpc_cidr_block" {
  description = "CIDR Block for VPC"
}

variable "aws_avail_zones" {
  description = "Availability Zones Used"
  type = "list"
}

variable "aws_cidr_subnets_private" {
  description = "CIDR Blocks for private subnets in Availability Zones"
  type = "list"
}

variable "aws_cidr_subnets_public" {
  description = "CIDR Blocks for public subnets in Availability Zones"
  type = "list"
}

//AWS EC2 Settings

variable "aws_bastion_ami" {
    description = "AMI ID for Bastion Host in chosen AWS Region"
}

variable "aws_bastion_size" {
    description = "EC2 Instance Size of Bastion Host"
}

/*
* AWS EC2 Settings
* The number should be divisable by the number of used
* AWS Availability Zones without an remainder.
*/
variable "aws_kube_master_num" {
    description = "Number of Kubernetes Master Nodes"
}

variable "aws_kube_master_size" {
    description = "Instance size of Kube Master Nodes"
}

variable "aws_etcd_num" {
    description = "Number of etcd Nodes"
}

variable "aws_etcd_size" {
    description = "Instance size of etcd Nodes"
}

variable "aws_kube_worker_num" {
    description = "Number of Kubernetes Worker Nodes"
}

variable "aws_kube_worker_size" {
    description = "Instance size of Kubernetes Worker Nodes"
}

variable "aws_cluster_ami" {
    description = "AMI ID for Kubernetes Cluster"
}
/*
* AWS ELB Settings
*
*/
variable "aws_elb_api_port" {
    description = "Port for AWS ELB"
}

variable "k8s_secure_api_port" {
    description = "Secure Port of K8S API Server"
}

variable "kube_insecure_apiserver_address" {
    description= "Bind Address for insecure Port of K8s API Server"
}
