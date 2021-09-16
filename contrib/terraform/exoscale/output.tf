output "master_ips" {
  value = module.kubernetes.master_ip_addresses
}

output "worker_ips" {
  value = module.kubernetes.worker_ip_addresses
}

output "ingress_controller_lb_ip_address" {
  value = module.kubernetes.ingress_controller_lb_ip_address
}

output "control_plane_lb_ip_address" {
  value = module.kubernetes.control_plane_lb_ip_address
}
