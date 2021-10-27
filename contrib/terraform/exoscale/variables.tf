variable "zone" {
  description = "The zone where to run the cluster"
}

variable "prefix" {
  description = "Prefix for resource names"
  default     = "default"
}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type = string
    size      = string
    boot_disk = object({
      image_name                = string
      root_partition_size       = number
      ceph_partition_size       = number
      node_local_partition_size = number
    })
  }))
}

variable "ssh_public_keys" {
  description = "List of public SSH keys which are injected into the VMs."
  type        = list(string)
}

variable "ssh_whitelist" {
  description = "List of IP ranges (CIDR) to whitelist for ssh"
  type        = list(string)
}

variable "api_server_whitelist" {
  description = "List of IP ranges (CIDR) to whitelist for kubernetes api server"
  type        = list(string)
}

variable "nodeport_whitelist" {
  description = "List of IP ranges (CIDR) to whitelist for kubernetes nodeports"
  type        = list(string)
}

variable "inventory_file" {
  description = "Where to store the generated inventory file"
}
