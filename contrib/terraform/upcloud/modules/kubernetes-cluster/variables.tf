variable "prefix" {
  type = string
}

variable "zone" {
  type = string
}

variable "template_name" {}

variable "username" {}

variable "private_network_cidr" {}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type       = string
    cpu             = string
    mem             = string
    disk_size       =  number
    additional_disks = map(object({
      size = number
      tier = string
    }))
  }))
}

variable "ssh_public_keys" {
  type = list(string)
}
