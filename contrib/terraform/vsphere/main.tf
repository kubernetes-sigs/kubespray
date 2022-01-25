provider "vsphere" {
  # Username and password set through env vars VSPHERE_USER and VSPHERE_PASSWORD
  user     = var.vsphere_user
  password = var.vsphere_password

  vsphere_server = var.vsphere_server

  # If you have a self-signed cert
  allow_unverified_ssl = true
}

data "vsphere_datacenter" "dc" {
  name = var.vsphere_datacenter
}

data "vsphere_datastore" "datastore" {
  name          = var.vsphere_datastore
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = var.network
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_virtual_machine" "template" {
  name          = var.template_name
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_compute_cluster" "compute_cluster" {
  name          = var.vsphere_compute_cluster
  datacenter_id = data.vsphere_datacenter.dc.id
}

resource "vsphere_resource_pool" "pool" {
  name                    = "${var.prefix}-cluster-pool"
  parent_resource_pool_id = data.vsphere_compute_cluster.compute_cluster.resource_pool_id
}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"

  prefix = var.prefix

  machines = var.machines

  ## Master ##
  master_cores     = var.master_cores
  master_memory    = var.master_memory
  master_disk_size = var.master_disk_size

  ## Worker ##
  worker_cores     = var.worker_cores
  worker_memory    = var.worker_memory
  worker_disk_size = var.worker_disk_size

  ## Global ##

  gateway       = var.gateway
  dns_primary   = var.dns_primary
  dns_secondary = var.dns_secondary

  pool_id      = vsphere_resource_pool.pool.id
  datastore_id = data.vsphere_datastore.datastore.id

  folder                = var.folder
  guest_id              = data.vsphere_virtual_machine.template.guest_id
  scsi_type             = data.vsphere_virtual_machine.template.scsi_type
  network_id            = data.vsphere_network.network.id
  adapter_type          = data.vsphere_virtual_machine.template.network_interface_types[0]
  interface_name        = var.interface_name
  firmware              = var.firmware
  hardware_version      = var.hardware_version
  disk_thin_provisioned = data.vsphere_virtual_machine.template.disks.0.thin_provisioned

  template_id = data.vsphere_virtual_machine.template.id
  vapp        = var.vapp

  ssh_public_keys = var.ssh_public_keys
}

#
# Generate ansible inventory
#

resource "local_file" "inventory" {
  content = templatefile("${path.module}/templates/inventory.tpl", {
    connection_strings_master = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s etcd_member_name=etcd%d",
      keys(module.kubernetes.master_ip),
      values(module.kubernetes.master_ip),
    range(1, length(module.kubernetes.master_ip) + 1))),
    connection_strings_worker = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s",
      keys(module.kubernetes.worker_ip),
    values(module.kubernetes.worker_ip))),
    list_master = join("\n", formatlist("%s", keys(module.kubernetes.master_ip))),
    list_worker = join("\n", formatlist("%s", keys(module.kubernetes.worker_ip)))
  })
  filename = var.inventory_file
}
