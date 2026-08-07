output "master_ip" {
  value = {
    for name, vm in opennebula_virtual_machine.master :
    vm.name => vm.nic[0].computed_ip
  }
}

output "worker_ip" {
  value = {
    for name, vm in opennebula_virtual_machine.worker :
    vm.name => vm.nic[0].computed_ip
  }
}
