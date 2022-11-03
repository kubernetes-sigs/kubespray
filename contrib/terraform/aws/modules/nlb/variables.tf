variable "aws_cluster_name" {
  description = "Name of Cluster"
}

variable "aws_vpc_id" {
  description = "AWS VPC ID"
}

variable "aws_nlb_api_port" {
  description = "Port for AWS NLB"
}

variable "k8s_secure_api_port" {
  description = "Secure Port of K8S API Server"
}

variable "aws_avail_zones" {
  description = "Availability Zones Used"
  type        = list(string)
}

variable "aws_subnet_ids_public" {
  description = "IDs of Public Subnets"
  type        = list(string)
}

variable "default_tags" {
  description = "Tags for all resources"
  type        = map(string)
}
