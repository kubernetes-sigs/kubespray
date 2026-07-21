variable "prefix" {}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type = string
    ip        = optional(string, "")
  }))
}

variable "template_id" {
  description = "ID of the existing contextualized OpenNebula VM template"
  type        = number
}

variable "template_disk_image_id" {
  description = "Image ID of the template's first disk (null when the template defines no image disk); required only for disk resizing"
  type        = number
  default     = null
}

variable "template_disk_size" {
  description = "SIZE (MB) declared on the template's first disk (0 = image default); used when re-declaring the OS disk"
  type        = number
  default     = 0
}

variable "network_id" {
  description = "ID of the OpenNebula Virtual Network the nodes attach to"
  type        = number
}

variable "master_cpu" {}
variable "master_vcpu" {}
variable "master_memory" {}
variable "master_disk_size" {}

variable "worker_cpu" {}
variable "worker_vcpu" {}
variable "worker_memory" {}
variable "worker_disk_size" {}

variable "ssh_public_keys" {
  type = list(string)
}

variable "vm_create_timeout" {}

variable "additional_disk_size" {
  default = 0
}

variable "image_datastore_name" {
  default = ""
}

variable "masters_anti_affinity" {
  type    = bool
  default = false
}

variable "network_reservation_size" {
  default = 0
}

variable "network_reservation_first_ip" {
  description = "First IP of the reservation carved from the parent network (empty = let OpenNebula choose)"
  default     = ""
}

variable "network_reservation_ar_id" {
  description = "Address-range ID of the parent network to reserve from (null = provider default)"
  type        = number
  default     = null
}
