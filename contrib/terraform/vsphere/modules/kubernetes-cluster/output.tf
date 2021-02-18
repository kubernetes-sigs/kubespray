output "worker_ip" {
  value = "${vsphere_virtual_machine.worker.*.default_ip_address}"
}

output "master_ip" {
  value = "${vsphere_virtual_machine.master.*.default_ip_address}"
}
