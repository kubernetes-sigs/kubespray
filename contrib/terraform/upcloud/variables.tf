
variable "zone" {
  description = "The zone where to run the cluster"
}

variable "hostname" {
  default = "example.com"
}

variable "template_name" {}

variable "username" {}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type = string
    cpu       = string
    mem       = string
    disk_size = number
  }))
}

variable "ssh_public_keys" {
  description = "List of public SSH keys which are injected into the VMs."
  type        = list(string)
}

variable "inventory_file" {
  description = "Where to store the generated inventory file"
}

variable "UPCLOUD_USERNAME" {}

variable "UPCLOUD_PASSWORD" {}
