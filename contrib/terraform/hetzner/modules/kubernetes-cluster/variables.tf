variable "zone" {
  type = string
}

variable "prefix" {}

variable "machines" {
  type = map(object({
    node_type = string
    size      = string
    image     = string
  }))
}

variable "ssh_public_keys" {
  type = list(string)
}

variable "ssh_whitelist" {
  type = list(string)
}

variable "api_server_whitelist" {
  type = list(string)
}

variable "nodeport_whitelist" {
  type = list(string)
}

variable "ingress_whitelist" {
  type = list(string)
}

variable "private_network_cidr" {
  default = "10.0.0.0/16"
}

variable "private_subnet_cidr" {
  default = "10.0.10.0/24"
}
variable "network_zone" {
  default = "eu-central"
}
