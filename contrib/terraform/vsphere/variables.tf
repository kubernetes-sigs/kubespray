## Global ##

variable "prefix" {
  default = ""
}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type = string
    ip        = string
  }))
}

variable "inventory_file" {
  default = "inventory.ini"
}

variable "network" {
  default = "VM Network"
}

variable "gateway" {}

variable "dns_primary" {
  default = "8.8.4.4"
}

variable "dns_secondary" {
  default = "8.8.8.8"
}

variable "vsphere_datacenter" {}

variable "vsphere_compute_cluster" {}

variable "vsphere_datastore" {}

variable "vsphere_user" {}

variable "vsphere_password" {}

variable "vsphere_server" {}

variable "vsphere_hostname" {}

variable "firmware" {
  default = "bios"
}

variable "hardware_version" {
  default = "15"
}

variable "template_name" {
  default = "ubuntu-focal-20.04-cloudimg"
}

variable "ssh_public_keys" {
  description = "List of public SSH keys which are injected into the VMs."
  type        = list(string)
}

## Master ##

variable "master_cores" {
  default = 4
}

variable "master_memory" {
  default = 4096
}

variable "master_disk_size" {
  default = "20"
}

## Worker ##

variable "worker_cores" {
  default = 16
}

variable "worker_memory" {
  default = 8192
}
variable "worker_disk_size" {
  default = "100"
}
