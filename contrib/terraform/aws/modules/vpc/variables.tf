variable "aws_vpc_cidr_block" {
  description = "CIDR Blocks for AWS VPC"
}

variable "aws_cluster_name" {
  description = "Name of Cluster"
}

variable "aws_avail_zones" {
  description = "AWS Availability Zones Used"
  type        = list(string)
}

variable "aws_cidr_subnets_private" {
  description = "CIDR Blocks for private subnets in Availability zones"
  type        = list(string)
}

variable "aws_cidr_subnets_public" {
  description = "CIDR Blocks for public subnets in Availability zones"
  type        = list(string)
}

variable "default_tags" {
  description = "Default tags for all resources"
  type        = map(string)
}

# NOTE: The previous default of cidr_blocks = ["0.0.0.0/0"] on the
# aws_security_group_rule "allow-ssh-connections" resource opened SSH (port 22)
# to the entire Internet for every instance in the shared kubernetes security
# group (bastion, control plane, worker, and etcd). This was a security risk:
# any instance with a public IP in that group was exposed to SSH brute force,
# and future topology changes could expose private-subnet instances as well.
# The default is now an empty list, which disables the rule entirely unless
# the caller explicitly supplies CIDRs via this variable.
variable "ssh_allowed_cidr_blocks" {
  description = "CIDRs allowed to SSH to cluster nodes; empty disables the rule"
  type        = list(string)
  default     = []
}
