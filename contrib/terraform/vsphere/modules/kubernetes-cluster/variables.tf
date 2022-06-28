## Global ##
variable "prefix" {}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type = string
    ip        = string
    netmask   = string
  }))
}

variable "gateway" {}
variable "dns_primary" {}
variable "dns_secondary" {}
variable "pool_id" {}
variable "datastore_id" {}
variable "guest_id" {}
variable "scsi_type" {}
variable "network_id" {}
variable "interface_name" {}
variable "adapter_type" {}
variable "disk_thin_provisioned" {}
variable "template_id" {}
variable "vapp" {
  type = bool
}
variable "firmware" {}
variable "folder" {}
variable "ssh_public_keys" {
  type = list(string)
}
variable "hardware_version" {}

## Master ##
variable "master_cores" {}
variable "master_memory" {}
variable "master_disk_size" {}

## Worker ##
variable "worker_cores" {}
variable "worker_memory" {}
variable "worker_disk_size" {}
