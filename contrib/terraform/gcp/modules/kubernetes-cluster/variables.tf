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
      size       = number
    })
  }))
}

variable "master_sa_email" {
  type = string
}

variable "master_sa_scopes" {
  type = list(string)
}

variable "master_preemptible" {
  type = bool
}

variable "master_additional_disk_type" {
  type = string
}

variable "worker_sa_email" {
  type = string
}

variable "worker_sa_scopes" {
  type = list(string)
}

variable "worker_preemptible" {
  type = bool
}

variable "worker_additional_disk_type" {
  type = string
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

variable "ingress_whitelist" {
  type = list(string)
  default = ["0.0.0.0/0"]
}

variable "private_network_cidr" {
  default = "10.0.10.0/24"
}

variable "extra_ingress_firewalls" {
  type = map(object({
    source_ranges = set(string)
    protocol      = string
    ports         = list(string)
    target_tags   = set(string)
  }))

  default = {}
}
