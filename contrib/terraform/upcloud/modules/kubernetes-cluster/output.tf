
output "master_ip" {
  value = {
    for instance in upcloud_server.master :
    instance.hostname => instance.network_interface[0].ip_address
  }
}

output "worker_ip" {
  value = {
    for instance in upcloud_server.worker :
    instance.hostname => instance.network_interface[0].ip_address
  }
}
