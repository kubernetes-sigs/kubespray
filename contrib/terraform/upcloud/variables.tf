variable "prefix" {
  type    = string
  default = "kubespray"

  description = "Prefix that is used to distinguish these resources from others"
}

variable "zone" {
  description = "The zone where to run the cluster"
}

variable "template_name" {
  description = "Block describing the preconfigured operating system"
}

variable "username" {
  description = "The username to use for the nodes"
  default     = "ubuntu"
}

variable "private_network_cidr" {
  description = "CIDR to use for the private network"
  default     = "172.16.0.0/24"
}

variable "machines" {
  description = "Cluster machines"

  type = map(object({
    node_type = string
    plan      = string
    cpu       = string
    mem       = string
    disk_size = number
    additional_disks = map(object({
      size = number
      tier = string
    }))
  }))
}

variable "ssh_public_keys" {
  description = "List of public SSH keys which are injected into the VMs."
  type        = list(string)
}

variable "inventory_file" {
  description = "Where to store the generated inventory file"
}

variable "UPCLOUD_USERNAME" {
  description = "UpCloud username with API access"
}

variable "UPCLOUD_PASSWORD" {
  description = "Password for UpCloud API user"
}

variable "firewall_enabled" {
  description = "Enable firewall rules"
  default     = false
}

variable "master_allowed_remote_ips" {
  description = "List of IP start/end addresses allowed to access API of masters"
  type = list(object({
    start_address = string
    end_address   = string
  }))
  default = []
}

variable "k8s_allowed_remote_ips" {
  description = "List of IP start/end addresses allowed to SSH to hosts"
  type = list(object({
    start_address = string
    end_address   = string
  }))
  default = []
}

variable "master_allowed_ports" {
  description = "List of ports to allow on masters"
  type = list(object({
    protocol       = string
    port_range_min = number
    port_range_max = number
    start_address  = string
    end_address    = string
  }))
}

variable "worker_allowed_ports" {
  description = "List of ports to allow on workers"
  type = list(object({
    protocol       = string
    port_range_min = number
    port_range_max = number
    start_address  = string
    end_address    = string
  }))
}

variable "firewall_default_deny_in" {
  description = "Add firewall policies that deny all inbound traffic by default"
  default     = false
}

variable "firewall_default_deny_out" {
  description = "Add firewall policies that deny all outbound traffic by default"
  default     = false
}

variable "loadbalancer_enabled" {
  description = "Enable load balancer"
  default     = false
}

variable "loadbalancer_plan" {
  description = "Load balancer plan (development/production-small)"
  default     = "development"
}

variable "loadbalancers" {
  description = "Load balancers"

  type = map(object({
    port            = number
    target_port     = number
    backend_servers = list(string)
  }))
  default = {}
}

variable "server_groups" {
  description = "Server groups"

  type = map(object({
    anti_affinity_policy = string
    servers              = list(string)
  }))

  default = {}
}
