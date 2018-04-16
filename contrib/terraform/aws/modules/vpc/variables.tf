variable "aws_vpc_cidr_block" {
    description = "CIDR Blocks for AWS VPC"
}


variable "aws_cluster_name" {
    description = "Name of Cluster"
}


variable "aws_avail_zones" {
    description = "AWS Availability Zones Used"
    type = "list"
}

variable "aws_cidr_subnets_private" {
  description = "CIDR Blocks for private subnets in Availability zones"
  type    = "list"
}

variable "aws_cidr_subnets_public" {
  description = "CIDR Blocks for public subnets in Availability zones"
  type    = "list"
}

variable "default_tags" {
  description = "Default tags for all resources"
  type = "map"
}
