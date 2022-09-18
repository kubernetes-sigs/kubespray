variable "zone" {
  description = "The zone where to run the cluster"
}
variable "network_zone" {
  description = "The network zone where the cluster is running"
  default = "eu-central"
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
    image     = string
  }))
}

variable "ssh_public_keys" {
  description = "Public SSH key which are injected into the VMs."
  type        = list(string)
}

variable "ssh_private_key_path" {
  description = "Private SSH key which connect to the VMs."
  type        = string
  default     = "~/.ssh/id_rsa"
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

variable "ingress_whitelist" {
  description = "List of IP ranges (CIDR) to whitelist for HTTP"
  type        = list(string)
}

variable "inventory_file" {
  description = "Where to store the generated inventory file"
}
