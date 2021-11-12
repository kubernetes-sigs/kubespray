output "master_ip" {
  value = {
    for name, machine in var.machines :
    name => machine.ip
    if machine.node_type == "master"
  }
}

output "worker_ip" {
  value = {
    for name, machine in var.machines :
    name => machine.ip
    if machine.node_type == "worker"
  }
}

