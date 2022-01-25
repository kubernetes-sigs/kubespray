output "customer_gateway_id" {
  description = "ID of the Customer Gateway"
  value       = element(concat(aws_customer_gateway.this.*.id, []), 0)
}

output "vpn_connection" {
  description = "VPN connection details"
  value = {
    id                            = element(concat(aws_vpn_connection.this.*.id, []), 0)
    transit_gateway_attachment_id = element(concat(aws_vpn_connection.this.*.transit_gateway_attachment_id, []), 0)
    tunnel1_address               = element(concat(aws_vpn_connection.this.*.tunnel1_address, []), 0)
    tunnel1_cgw_inside_address    = element(concat(aws_vpn_connection.this.*.tunnel1_cgw_inside_address, []), 0)
    tunnel1_vgw_inside_address    = element(concat(aws_vpn_connection.this.*.tunnel1_vgw_inside_address, []), 0)
    tunnel2_address               = element(concat(aws_vpn_connection.this.*.tunnel2_address, []), 0)
    tunnel2_cgw_inside_address    = element(concat(aws_vpn_connection.this.*.tunnel2_cgw_inside_address, []), 0)
    tunnel2_vgw_inside_address    = element(concat(aws_vpn_connection.this.*.tunnel2_vgw_inside_address, []), 0)
  }
}
