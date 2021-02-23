output "master_ip_addresses" {
  value = module.kubernetes.master_ip
}

output "worker_ip_addresses" {
  value = module.kubernetes.worker_ip
}

output "vsphere_datacenter" {
  value = var.vsphere_datacenter
}

output "vsphere_server" {
  value = var.vsphere_server
}

output "vsphere_datastore" {
  value = var.vsphere_datastore
}

output "vsphere_network" {
  value = var.network
}

output "vsphere_folder" {
  value = terraform.workspace
}

output "vsphere_pool" {
  value = "${terraform.workspace}-cluster-pool"
}
