output "master_ip_addresses" {
  value = {
    for key, instance in hcloud_server.master :
    instance.name => {
      "private_ip" = hcloud_server_network.master[key].ip
      "public_ip"  = hcloud_server.master[key].ipv4_address
    }
  }
}

output "worker_ip_addresses" {
  value = {
    for key, instance in hcloud_server.worker :
    instance.name => {
      "private_ip" = hcloud_server_network.worker[key].ip
      "public_ip"  = hcloud_server.worker[key].ipv4_address
    }
  }
}

output "cluster_private_network_cidr" {
  value = var.private_subnet_cidr
}

output "network_id" {
  value = hcloud_network.kubernetes.id
}
