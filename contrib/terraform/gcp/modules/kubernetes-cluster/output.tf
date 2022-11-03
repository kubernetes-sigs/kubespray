output "master_ip_addresses" {
  value = {
    for key, instance in google_compute_instance.master :
    instance.name => {
      "private_ip" = instance.network_interface.0.network_ip
      "public_ip"  = instance.network_interface.0.access_config.0.nat_ip
    }
  }
}

output "worker_ip_addresses" {
  value = {
    for key, instance in google_compute_instance.worker :
    instance.name => {
      "private_ip" = instance.network_interface.0.network_ip
      "public_ip"  = instance.network_interface.0.access_config.0.nat_ip
    }
  }
}

output "ingress_controller_lb_ip_address" {
  value = length(var.ingress_whitelist) > 0 ? google_compute_address.worker_lb.0.address : ""
}

output "control_plane_lb_ip_address" {
  value = length(var.api_server_whitelist) > 0 ? google_compute_forwarding_rule.master_lb.0.ip_address : ""
}
