output "master_ip_addresses" {
  value = module.kubernetes.master_ip
}

output "worker_ip_addresses" {
  value = module.kubernetes.worker_ip
}

output "one_template" {
  value = var.template_name
}

output "one_network" {
  value = var.network_name
}
