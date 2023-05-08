output "master_ip_addresses" {
  value = {
    for name, machine in var.machines :
      name => {
        "private_ip" = hcloud_server_network.machine[name].ip
        "public_ip"  = hcloud_server.machine[name].ipv4_address
      }
      if machine.node_type == "master"
  }
}

output "worker_ip_addresses" {
  value = {
    for name, machine in var.machines :
      name => {
        "private_ip" = hcloud_server_network.machine[name].ip
        "public_ip"  = hcloud_server.machine[name].ipv4_address
      }
      if machine.node_type == "worker"
  }
}

output "cluster_private_network_cidr" {
  value = var.private_subnet_cidr
}

output "network_id" {
  value = hcloud_network.kubernetes.id
}
