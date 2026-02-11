variable "prefix" {
  type = string
}

variable "zone" {
  type = string
}

variable "private_cloud" {
  type = bool
}

variable "public_zone" {
  type = string
}

variable "template_name" {}

variable "username" {}

variable "private_network_cidr" {}

variable "dns_servers" {}

variable "use_public_ips" {}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type         = string
    plan              = string
    cpu               = optional(number)
    mem               = optional(number)
    disk_size         = number
    template_name     = optional(string)
    boot_disk_encrypt = optional(bool, false)
    server_group : optional(string, null)
    force_public_ip : optional(bool, false)
    dns_servers : optional(set(string))
    additional_disks = map(object({
      size = number
      tier = string
    }))
    metadata : optional(bool, false)
  }))
}

variable "ssh_public_keys" {
  type = list(string)
}

variable "firewall_enabled" {
  type = bool
}

variable "master_allowed_remote_ips" {
  type = list(object({
    start_address = string
    end_address   = string
  }))
}

variable "k8s_allowed_remote_ips" {
  type = list(object({
    start_address = string
    end_address   = string
  }))
}

variable "bastion_allowed_remote_ips" {
  type = list(object({
    start_address = string
    end_address   = string
  }))
}

variable "master_allowed_ports" {
  type = list(object({
    protocol       = string
    port_range_min = number
    port_range_max = number
    start_address  = string
    end_address    = string
  }))
}

variable "worker_allowed_ports" {
  type = list(object({
    protocol       = string
    port_range_min = number
    port_range_max = number
    start_address  = string
    end_address    = string
  }))
}

variable "firewall_default_deny_in" {
  type = bool
}

variable "firewall_default_deny_out" {
  type = bool
}

variable "loadbalancer_enabled" {
  type = bool
}

variable "loadbalancers" {
  description = "Load balancers"

  type = map(object({
    plan            = string
    legacy_network  = bool
    public_network  = bool
    private_network = bool

    floating_ip              = optional(string)
    floating_ip_network_name = optional(string)

    targets = map(object({
      proxy_protocol  = bool
      port            = number
      target_port     = number
      listen_public   = bool
      listen_private  = bool
      backend_servers = list(string)
    }))
  }))

  validation {
    condition = alltrue([
      for _, lb in var.loadbalancers :
      (
        try(lb.floating_ip, null) == null ||
        try(lb.floating_ip_network_name, null) != null
      )
    ])
    error_message = "If floating_ip is set, floating_ip_network_name must also be set."
  }

  default = {}
}

variable "server_groups" {
  description = "Server groups"

  type = map(object({
    anti_affinity_policy = string
  }))
}

variable "router_enable" {
  description = "If a router should be enabled and connected to the private network or not"

  type = bool
}

variable "gateways" {
  description = "Gateways that should be connected to the router, requires router_enable is set to true"

  type = map(object({
    features = list(string)
    plan     = optional(string)
    connections = optional(map(object({
      type = string
      local_routes = optional(map(object({
        type           = string
        static_network = string
      })))
      remote_routes = optional(map(object({
        type           = string
        static_network = string
      })))
      tunnels = optional(map(object({
        remote_address = string
        ipsec_properties = optional(object({
          child_rekey_time            = number
          dpd_delay                   = number
          dpd_timeout                 = number
          ike_lifetime                = number
          rekey_time                  = number
          phase1_algorithms           = set(string)
          phase1_dh_group_numbers     = set(string)
          phase1_integrity_algorithms = set(string)
          phase2_algorithms           = set(string)
          phase2_dh_group_numbers     = set(string)
          phase2_integrity_algorithms = set(string)
        }))
      })))
    })))
  }))
}

variable "gateway_vpn_psks" {
  description = "Separate variable for providing psks for connection tunnels"

  type = map(object({
    psk = string
  }))
  default   = {}
  sensitive = true
}

variable "static_routes" {
  description = "Static routes to apply to the router, requires router_enable is set to true"

  type = map(object({
    nexthop = string
    route   = string
  }))
}

variable "network_peerings" {
  description = "Other UpCloud private networks to peer with, requires router_enable is set to true"

  type = map(object({
    remote_network = string
  }))
}