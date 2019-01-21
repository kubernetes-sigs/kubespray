variable "external_net" {}

variable "network_name" {}

variable "bastion_network_name" {}

variable "cluster_name" {}

variable "dns_nameservers" {
  type = "list"
}

variable "subnet_cidr" {}

variable "use_neutron" {}

variable "network_router_extra_routes" {
  type = "map"
}

variable "bastion_subnet_extra_routes" {
  type = "map"
}
