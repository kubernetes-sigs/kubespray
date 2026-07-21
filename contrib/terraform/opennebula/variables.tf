## OpenNebula connection. Leave empty to use the OPENNEBULA_ENDPOINT,
## OPENNEBULA_USERNAME, OPENNEBULA_PASSWORD and OPENNEBULA_INSECURE
## environment variables.

variable "one_endpoint" {
  description = "OpenNebula XML-RPC API endpoint, e.g. https://one.example.com:2634/RPC2"
  default     = ""
}

variable "one_username" {
  default = ""
}

variable "one_password" {
  default   = ""
  sensitive = true
}

variable "one_insecure" {
  description = "Skip TLS certificate verification of the OpenNebula endpoint"
  type        = bool
  default     = false
}

## Cluster

variable "prefix" {
  default = "k8s"
}

variable "inventory_file" {
  default = "inventory.ini"
}

variable "template_name" {
  description = "Name of the existing contextualized OpenNebula VM template"
}

variable "network_name" {
  description = "Name of the existing OpenNebula Virtual Network the nodes attach to"
}

variable "master_count" {
  description = "Number of control-plane nodes to create (named master-0..N-1); ignored when machines is set"
  type        = number
  default     = 0

  validation {
    condition     = var.master_count >= 0
    error_message = "master_count must be >= 0."
  }
}

variable "worker_count" {
  description = "Number of worker nodes to create (named worker-0..N-1); ignored when machines is set"
  type        = number
  default     = 0

  validation {
    condition     = var.worker_count >= 0
    error_message = "worker_count must be >= 0."
  }
}

variable "machines" {
  description = "Advanced node definition (named nodes, optional static IPs); takes precedence over master_count/worker_count when non-empty"
  type = map(object({
    node_type = string
    ip        = optional(string, "")
  }))
  default = {}

  validation {
    condition = alltrue([
      for machine in var.machines : contains(["master", "worker"], machine.node_type)
    ])
    error_message = "machines[*].node_type must be \"master\" or \"worker\"."
  }
}

variable "ssh_public_keys" {
  description = "List of public SSH keys which are injected into the VMs."
  type        = list(string)
}

variable "ansible_user" {
  description = "SSH user written into the generated inventory (the user one-context injects keys for; root on standard OpenNebula images)"
  default     = "root"
}

## Master

variable "master_cpu" {
  default = 1
}

variable "master_vcpu" {
  default = 2
}

variable "master_memory" {
  description = "Memory in MB"
  default     = 4096
}

variable "master_disk_size" {
  description = "OS disk size in MB; 0 keeps the template's disk unchanged"
  default     = 0

  validation {
    condition     = var.master_disk_size >= 0
    error_message = "master_disk_size must be >= 0 (MB)."
  }
}

## Worker

variable "worker_cpu" {
  default = 1
}

variable "worker_vcpu" {
  default = 4
}

variable "worker_memory" {
  description = "Memory in MB"
  default     = 8192
}

variable "worker_disk_size" {
  description = "OS disk size in MB; 0 keeps the template's disk unchanged"
  default     = 0

  validation {
    condition     = var.worker_disk_size >= 0
    error_message = "worker_disk_size must be >= 0 (MB)."
  }
}

variable "vm_create_timeout" {
  default = "20m"
}

## OpenNebula extras

variable "additional_disk_size" {
  description = "Size (MB) of an extra DATABLOCK disk attached to every node; 0 disables it"
  default     = 0

  validation {
    condition     = var.additional_disk_size >= 0
    error_message = "additional_disk_size must be >= 0 (MB)."
  }
}

variable "image_datastore_name" {
  description = "IMAGE datastore for the additional DATABLOCK disk (required when additional_disk_size > 0)"
  default     = ""
}

variable "masters_anti_affinity" {
  description = "Spread master VMs across hosts using an ANTI_AFFINED VM group"
  type        = bool
  default     = false
}

variable "network_reservation_size" {
  description = "If > 0, create a reservation of this many addresses from network_name and attach the nodes to it"
  default     = 0

  validation {
    condition     = var.network_reservation_size >= 0
    error_message = "network_reservation_size must be >= 0."
  }
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
