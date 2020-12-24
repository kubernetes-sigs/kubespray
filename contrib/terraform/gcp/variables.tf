variable keyfile_location {
  description = "Location of the json keyfile to use with the google provider"
  type        = string
}

variable region {
  description = "Region of all resources"
  type        = string
}

variable gcp_project_id {
  description = "ID of the project"
  type        = string
}

variable prefix {
  description = "Prefix for resource names"
  default     = "default"
}

variable machines {
  description = "Cluster machines"
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
  type    = string
  default = ""
}

variable "master_sa_scopes" {
  type    = list(string)
  default = ["https://www.googleapis.com/auth/cloud-platform"]
}

variable "worker_sa_email" {
  type    = string
  default = ""
}

variable "worker_sa_scopes" {
  type    = list(string)
  default = ["https://www.googleapis.com/auth/cloud-platform"]
}

variable ssh_pub_key {
  description = "Path to public SSH key file which is injected into the VMs."
  type        = string
}

variable ssh_whitelist {
  type = list(string)
}

variable api_server_whitelist {
  type = list(string)
}

variable nodeport_whitelist {
  type = list(string)
}
