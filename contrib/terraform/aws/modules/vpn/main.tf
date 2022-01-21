# Create Customer Gateway
resource "aws_customer_gateway" "this" {
  bgp_asn    = var.customer_side_asn
  ip_address = var.customer_gateway_ip_address
  type       = "ipsec.1"

  tags = merge(
    tomap({
      Name = "kubernetes-${var.aws_cluster_name}-cgw"
    }),
    var.default_tags,
    var.cgw_tags,
  )
}

# Customer Gateway - Transit Gateway VPN Connection
resource "aws_vpn_connection" "this" {
  transit_gateway_id         = var.transit_gateway_id
  customer_gateway_id        = aws_customer_gateway.this.id
  type                       = "ipsec.1"
  static_routes_only         = var.vpn_connection_static_routes_only
  local_ipv4_network_cidr    = var.vpn_connection_local_ipv4_network_cidr
  remote_ipv4_network_cidr   = var.vpn_connection_remote_ipv4_network_cidr

  tunnel1_dpd_timeout_action = var.vpn_connection_tunnel1_dpd_timeout_action
  tunnel1_ike_versions       = var.vpn_connection_tunnel1_ike_versions
  tunnel1_inside_cidr        = var.vpn_connection_tunnel1_inside_cidr
  tunnel1_preshared_key      = var.vpn_connection_tunnel1_preshared_key
  tunnel1_startup_action     = var.vpn_connection_tunnel1_startup_action

  tunnel1_phase1_dh_group_numbers      = var.vpn_connection_tunnel1_phase1_dh_group_numbers
  tunnel1_phase2_dh_group_numbers      = var.vpn_connection_tunnel1_phase2_dh_group_numbers
  tunnel1_phase1_encryption_algorithms = var.vpn_connection_tunnel1_phase1_encryption_algorithms
  tunnel1_phase2_encryption_algorithms = var.vpn_connection_tunnel1_phase2_encryption_algorithms
  tunnel1_phase1_integrity_algorithms  = var.vpn_connection_tunnel1_phase1_integrity_algorithms
  tunnel1_phase2_integrity_algorithms  = var.vpn_connection_tunnel1_phase2_integrity_algorithms

  tunnel2_dpd_timeout_action = var.vpn_connection_tunnel2_dpd_timeout_action
  tunnel2_ike_versions       = var.vpn_connection_tunnel2_ike_versions
  tunnel2_inside_cidr        = var.vpn_connection_tunnel2_inside_cidr
  tunnel2_preshared_key      = var.vpn_connection_tunnel2_preshared_key
  tunnel2_startup_action     = var.vpn_connection_tunnel2_startup_action

  tunnel2_phase1_dh_group_numbers      = var.vpn_connection_tunnel2_phase1_dh_group_numbers
  tunnel2_phase2_dh_group_numbers      = var.vpn_connection_tunnel2_phase2_dh_group_numbers
  tunnel2_phase1_encryption_algorithms = var.vpn_connection_tunnel2_phase1_encryption_algorithms
  tunnel2_phase2_encryption_algorithms = var.vpn_connection_tunnel2_phase2_encryption_algorithms
  tunnel2_phase1_integrity_algorithms  = var.vpn_connection_tunnel2_phase1_integrity_algorithms
  tunnel2_phase2_integrity_algorithms  = var.vpn_connection_tunnel2_phase2_integrity_algorithms

  tags = merge(
    tomap({
      Name = "kubernetes-${var.aws_cluster_name}-vpnConnection"
    }),
    var.default_tags,
    var.vpn_connection_tags,
  )
}

# Add route
resource "aws_ec2_transit_gateway_route" "this" {
  destination_cidr_block = var.local_cidr
  blackhole              = null

  transit_gateway_route_table_id = var.transit_gateway_route_table_id
  transit_gateway_attachment_id  = aws_vpn_connection.this.transit_gateway_attachment_id
}

# route table association and propagation
resource "aws_ec2_transit_gateway_route_table_association" "this" {
  transit_gateway_route_table_id = var.transit_gateway_route_table_id
  transit_gateway_attachment_id  = aws_vpn_connection.this.transit_gateway_attachment_id
}

resource "aws_ec2_transit_gateway_route_table_propagation" "this" {
  count = var.propagateion_enable ? 1 : 0

  transit_gateway_route_table_id = var.transit_gateway_route_table_id
  transit_gateway_attachment_id  = aws_vpn_connection.this.transit_gateway_attachment_id
}
