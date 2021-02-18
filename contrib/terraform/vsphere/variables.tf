## Global ##

variable prefix {
  default = ""
}

variable "network" {
  default = "VM Network"
}

variable "ip_prefix" {
  default = ""
}

variable "ip_last_octet_start_number_master" {
  default = ""
}

variable "ip_last_octet_start_number_worker" {
  default = ""
}

variable "gateway" {
  default = ""
}

variable "dns_primary" {
  default = ""
}

variable "dns_secondary" {
  default = ""
}

variable "vsphere_datacenter" {
  default = ""
}

variable "vsphere_compute_cluster" {
  default = ""
}

variable "vsphere_datastore" {
  default= ""
}

variable "vsphere_server" {
  default = ""
}

variable "vsphere_hostname" {
  default = ""
}

variable "firmware" {
  default = "bios"
}

variable "hardware_version" {
  default = "15"
}

variable "template_name" {
  default = "ubuntu-focal-20.04-cloudimg"
}

variable "ssh_pub_key" {
  default = ""
}

## Master ##
variable "master_count" {
  default = "1"
}
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

variable "worker_count" {
  default = "1"
}
variable "worker_cores" {
  default = 16
}

variable "worker_memory" {
  default = 8192
}
variable "worker_disk_size" {
  default = "100"
}
