#Global Vars
aws_cluster_name = "devtest"

#VPC Vars
aws_vpc_cidr_block       = "10.0.0.0/16"
aws_cidr_subnets_private = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
aws_cidr_subnets_public = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

#Bastion Host
aws_bastion_num  = 1
aws_bastion_size = "t2.medium"


#Kubernetes Cluster
aws_kube_master_num  = 3
aws_kube_master_size = "t2.medium"
aws_kube_master_disk_size = 50

aws_etcd_num  = 0
aws_etcd_size = "t2.medium"
aws_etcd_disk_size = 50

aws_kube_worker_num  = 2
aws_kube_worker_size = "t2.medium"
aws_kube_worker_disk_size = 50


#EC2 Source/Dest Check
aws_src_dest_check      = false

#Settings AWS ELB
aws_elb_api_port          = 6443
k8s_secure_api_port       = 6443
aws_elb_api_internal      = true
aws_elb_api_public_subnet = true

default_tags = {
  #  Env = "devtest"
  #  Product = "kubernetes"
}

inventory_file = "../../../inventory/hosts"
