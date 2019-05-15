variable "external_net" {}

variable "network_name" {}

variable "cluster_name" {}

variable "dns_nameservers" {
  type = "list"
}

variable "subnet_cidr" {}

variable "use_neutron" {}
