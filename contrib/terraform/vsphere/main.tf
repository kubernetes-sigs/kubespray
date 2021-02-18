provider "vsphere" {
  # Username and password set through env vars VSPHERE_USER and VSPHERE_PASSWORD
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
  name          = "VM Network"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_host" "host" {
  name          = var.vsphere_hostname
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
  parent_resource_pool_id = data.vsphere_host.host.resource_pool_id
}

module "kubernetes" {
  source        = "./modules/kubernetes-cluster"

  prefix = var.prefix

  ## Master ##
  master_count      = var.master_count
  master_cores      = var.master_cores
  master_memory     = var.master_memory
  master_disk_size  = var.master_disk_size

  ## Worker ##
  worker_count      = var.worker_count
  worker_cores      = var.worker_cores
  worker_memory     = var.worker_memory
  worker_disk_size  = var.worker_disk_size

  ## Global ##

  ip_prefix                         = var.ip_prefix
  ip_last_octet_start_number_master = var.ip_last_octet_start_number_master
  ip_last_octet_start_number_worker = var.ip_last_octet_start_number_worker
  gateway                           = var.gateway
  dns_primary                       = var.dns_primary
  dns_secondary                     = var.dns_secondary

  pool_id       = vsphere_resource_pool.pool.id
  datastore_id  = data.vsphere_datastore.datastore.id

  folder                = ""
  guest_id              = data.vsphere_virtual_machine.template.guest_id
  scsi_type             = data.vsphere_virtual_machine.template.scsi_type
  network_id            = data.vsphere_network.network.id
  adapter_type          = data.vsphere_virtual_machine.template.network_interface_types[0]
  firmware              = var.firmware
  hardware_version      = var.hardware_version
  disk_thin_provisioned = data.vsphere_virtual_machine.template.disks.0.thin_provisioned

  template_id   = data.vsphere_virtual_machine.template.id

  ssh_pub_key   = var.ssh_pub_key
}
