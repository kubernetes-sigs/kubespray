variable "aws_cluster_name" {
  description = "Name of Cluster"
}

variable "customer_side_asn" {
  description = "The Autonomous System Number (ASN) for the Customer side of the gateway."
  type        = string
  default     = "65000"
}

variable "customer_gateway_ip_address" {
  type        = string
  description = "The IP address of the gateway's Internet-routable external interface"
}

# VPN Connection

variable "transit_gateway_id" {
  type        = string
  description = "Transit gateway ID"
} 

variable "vpn_connection_static_routes_only" {
  type        = string
  description = "If set to `true`, the VPN connection will use static routes exclusively. Static routes must be used for devices that don't support BGP"
  default     = "true"
}

variable "vpn_connection_local_ipv4_network_cidr" {
  type        = string
  description = "The IPv4 CIDR on the customer gateway (on-premises) side of the VPN connection."
  default     = "0.0.0.0/0"
}

variable "local_cidr" {
  type        = string
  description = "The IPv4 CIDR of Local"
}

variable "vpn_connection_remote_ipv4_network_cidr" {
  type        = string
  description = "The IPv4 CIDR on the AWS side of the VPN connection."
  default     = "0.0.0.0/0"
}

variable "vpn_connection_tunnel1_dpd_timeout_action" {
  type        = string
  description = "The action to take after DPD timeout occurs for the first VPN tunnel. Specify restart to restart the IKE initiation. Specify clear to end the IKE session. Valid values are clear | none | restart."
  default     = "clear"
}

variable "vpn_connection_tunnel1_ike_versions" {
  type        = list(string)
  description = "The IKE versions that are permitted for the first VPN tunnel. Valid values are ikev1 | ikev2."
  default     = []
}

variable "vpn_connection_tunnel1_inside_cidr" {
  type        = string
  description = "The CIDR block of the inside IP addresses for the first VPN tunnel"
  default     = null
}

variable "vpn_connection_tunnel1_preshared_key" {
  type        = string
  description = "The preshared key of the first VPN tunnel. The preshared key must be between 8 and 64 characters in length and cannot start with zero. Allowed characters are alphanumeric characters, periods(.) and underscores(_)"
  default     = null
}

variable "vpn_connection_tunnel1_startup_action" {
  type        = string
  description = "The action to take when the establishing the tunnel for the first VPN connection. By default, your customer gateway device must initiate the IKE negotiation and bring up the tunnel. Specify start for AWS to initiate the IKE negotiation. Valid values are add | start."
  default     = "add"
}

variable "vpn_connection_tunnel1_phase1_dh_group_numbers" {
  type        = list(string)
  description = "List of one or more Diffie-Hellman group numbers that are permitted for the first VPN tunnel for phase 1 IKE negotiations. Valid values are 2 | 5 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24."
  default     = []
}

variable "vpn_connection_tunnel1_phase2_dh_group_numbers" {
  type        = list(string)
  description = "List of one or more Diffie-Hellman group numbers that are permitted for the first VPN tunnel for phase 2 IKE negotiations. Valid values are 2 | 5 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24."
  default     = []
}

variable "vpn_connection_tunnel1_phase1_encryption_algorithms" {
  type        = list(string)
  description = "List of one or more encryption algorithms that are permitted for the first VPN tunnel for phase 1 IKE negotiations. Valid values are AES128 | AES256 | AES128-GCM-16 | AES256-GCM-16."
  default     = []
}

variable "vpn_connection_tunnel1_phase2_encryption_algorithms" {
  type        = list(string)
  description = "List of one or more encryption algorithms that are permitted for the first VPN tunnel for phase 2 IKE negotiations. Valid values are AES128 | AES256 | AES128-GCM-16 | AES256-GCM-16."
  default     = []
}

variable "vpn_connection_tunnel1_phase1_integrity_algorithms" {
  type        = list(string)
  description = "One or more integrity algorithms that are permitted for the first VPN tunnel for phase 1 IKE negotiations. Valid values are SHA1 | SHA2-256 | SHA2-384 | SHA2-512."
  default     = []
}

variable "vpn_connection_tunnel1_phase2_integrity_algorithms" {
  type        = list(string)
  description = "One or more integrity algorithms that are permitted for the first VPN tunnel for phase 2 IKE negotiations. Valid values are SHA1 | SHA2-256 | SHA2-384 | SHA2-512."
  default     = []
}

variable "vpn_connection_tunnel2_dpd_timeout_action" {
  type        = string
  description = "The action to take after DPD timeout occurs for the second VPN tunnel. Specify restart to restart the IKE initiation. Specify clear to end the IKE session. Valid values are clear | none | restart."
  default     = "clear"
}

variable "vpn_connection_tunnel2_ike_versions" {
  type        = list(string)
  description = "The IKE versions that are permitted for the second VPN tunnel. Valid values are ikev1 | ikev2."
  default     = []
}

variable "vpn_connection_tunnel2_inside_cidr" {
  type        = string
  description = "The CIDR block of the inside IP addresses for the second VPN tunnel"
  default     = null
}

variable "vpn_connection_tunnel2_preshared_key" {
  type        = string
  description = "The preshared key of the second VPN tunnel. The preshared key must be between 8 and 64 characters in length and cannot start with zero. Allowed characters are alphanumeric characters, periods(.) and underscores(_)"
  default     = null
}

variable "vpn_connection_tunnel2_startup_action" {
  type        = string
  description = "The action to take when the establishing the tunnel for the second VPN connection. By default, your customer gateway device must initiate the IKE negotiation and bring up the tunnel. Specify start for AWS to initiate the IKE negotiation. Valid values are add | start."
  default     = "add"
}

variable "vpn_connection_tunnel2_phase1_dh_group_numbers" {
  type        = list(string)
  description = "List of one or more Diffie-Hellman group numbers that are permitted for the second VPN tunnel for phase 1 IKE negotiations. Valid values are 2 | 5 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24."
  default     = []
}

variable "vpn_connection_tunnel2_phase2_dh_group_numbers" {
  type        = list(string)
  description = "List of one or more Diffie-Hellman group numbers that are permitted for the second VPN tunnel for phase 2 IKE negotiations. Valid values are 2 | 5 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24."
  default     = []
}

variable "vpn_connection_tunnel2_phase1_encryption_algorithms" {
  type        = list(string)
  description = "List of one or more encryption algorithms that are permitted for the second VPN tunnel for phase 1 IKE negotiations. Valid values are AES128 | AES256 | AES128-GCM-16 | AES256-GCM-16."
  default     = []
}

variable "vpn_connection_tunnel2_phase2_encryption_algorithms" {
  type        = list(string)
  description = "List of one or more encryption algorithms that are permitted for the second VPN tunnel for phase 2 IKE negotiations. Valid values are AES128 | AES256 | AES128-GCM-16 | AES256-GCM-16."
  default     = []
}

variable "vpn_connection_tunnel2_phase1_integrity_algorithms" {
  type        = list(string)
  description = "One or more integrity algorithms that are permitted for the second VPN tunnel for phase 1 IKE negotiations. Valid values are SHA1 | SHA2-256 | SHA2-384 | SHA2-512."
  default     = []
}

variable "vpn_connection_tunnel2_phase2_integrity_algorithms" {
  type        = list(string)
  description = "One or more integrity algorithms that are permitted for the second VPN tunnel for phase 2 IKE negotiations. Valid values are SHA1 | SHA2-256 | SHA2-384 | SHA2-512."
  default     = []
}

variable "transit_gateway_route_table_id" {
  description = "Identifier of EC2 Transit Gateway Route Table to use with the Target Gateway when reusing it between multiple TGWs"
  type        = string
  default     = null
}

variable "propagateion_enable" {
  description = "Propagateion enable"
  type        = bool
  default     = false
}

# Tags
variable "default_tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

variable "cgw_tags" {
  description = "Additional tags for the CGW"
  type        = map(string)
  default     = {}
}

variable "vpn_connection_tags" {
  description = "Additional tags for the VPN Connection"
  type        = map(string)
  default     = {}
}
