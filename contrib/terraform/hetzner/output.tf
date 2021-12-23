output "master_ips" {
  value = module.kubernetes.master_ip_addresses
}

output "worker_ips" {
  value = module.kubernetes.worker_ip_addresses
}
