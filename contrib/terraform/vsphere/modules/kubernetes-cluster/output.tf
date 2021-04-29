output "master_ip" {
  value = {
    for instance in vsphere_virtual_machine.master :
    instance.name => instance.default_ip_address
  }
}

output "worker_ip" {
  value = {
    for instance in vsphere_virtual_machine.worker :
    instance.name => instance.default_ip_address
  }
}
