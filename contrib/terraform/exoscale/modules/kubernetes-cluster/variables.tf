variable "zone" {
  type = string
  # This is currently the only zone that is supposed to be supporting
  # so called "managed private networks".
  # See: https://www.exoscale.com/syslog/introducing-managed-private-networks
  default = "ch-gva-2"
}

variable "prefix" {}

variable "machines" {
  type = map(object({
    node_type = string
    size      = string
    boot_disk = object({
      image_name                = string
      root_partition_size       = number
      ceph_partition_size       = number
      node_local_partition_size = number
    })
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

variable "private_network_cidr" {
  default = "172.0.10.0/24"
}
