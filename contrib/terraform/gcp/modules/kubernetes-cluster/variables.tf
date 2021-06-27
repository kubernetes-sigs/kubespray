variable "region" {
  type = string
}

variable "prefix" {}

variable "machines" {
  type = map(object({
    node_type = string
    size      = string
    zone      = string
    additional_disks = map(object({
      size = number
    }))
    boot_disk = object({
      image_name = string
      size = number
    })
  }))
}

variable "master_sa_email" {
  type = string
}

variable "master_sa_scopes" {
  type = list(string)
}

variable "worker_sa_email" {
  type = string
}

variable "worker_sa_scopes" {
  type = list(string)
}

variable "ssh_pub_key" {}

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
  default = "10.0.10.0/24"
}
