resource "vsphere_virtual_machine" "worker" {
  count               = var.worker_count
  name                = "${var.prefix}-worker-${count.index}"
  resource_pool_id    = var.pool_id
  datastore_id        = var.datastore_id

  num_cpus            = var.worker_cores
  memory              = var.worker_memory
  memory_reservation  = var.worker_memory
  guest_id            = var.guest_id
  enable_disk_uuid    = "true"
  scsi_type           = var.scsi_type
  folder              = var.folder
  firmware            = var.firmware
  hardware_version    = var.hardware_version

  wait_for_guest_net_routable = false

  network_interface {
    network_id        = var.network_id
    adapter_type      = var.adapter_type
  }

  disk {
    label             = "disk0"
    size              = var.worker_disk_size
    thin_provisioned  = var.disk_thin_provisioned
  }

  lifecycle {
    ignore_changes    = [disk]
  }

  clone {
    template_uuid     = var.template_id
  }

  cdrom {
    client_device = true
  }

  vapp {
    properties = {
      "user-data" = base64encode(templatefile("/home/jakub/workspace/ck8s/compliantkubernetes-kubespray/kubespray/contrib/terraform/vsphere/cloud-init.yaml", { ip = "${var.ip_prefix}.${count.index + var.ip_last_octet_start_number_worker}/28",
                                                                  gw = "${var.gateway}",
                                                                  dns = "${var.dns_primary}",
                                                                  ssh_pub_key = "${file(var.ssh_pub_key)}"}))
    }
  }
}

resource "vsphere_virtual_machine" "master" {
  count               = var.master_count
  name                = "${var.prefix}-master-${count.index}"
  resource_pool_id    = var.pool_id
  datastore_id        = var.datastore_id

  num_cpus            = var.master_cores
  memory              = var.master_memory
  memory_reservation  = var.master_memory
  guest_id            = var.guest_id
  enable_disk_uuid    = "true"
  scsi_type           = var.scsi_type
  folder              = var.folder
  firmware            = var.firmware
  hardware_version    = var.hardware_version

  network_interface {
    network_id        = var.network_id
    adapter_type      = var.adapter_type
  }

  disk {
    label             = "disk0"
    size              = var.master_disk_size
    thin_provisioned  = var.disk_thin_provisioned
  }

  lifecycle {
    ignore_changes    = [disk]
  }

  clone {
    template_uuid     = var.template_id
  }

  cdrom {
    client_device = true
  }

  vapp {
    properties = {
      "user-data" = base64encode(templatefile("/home/jakub/workspace/ck8s/compliantkubernetes-kubespray/kubespray/contrib/terraform/vsphere/cloud-init.yaml", { ip = "${var.ip_prefix}.${count.index + var.ip_last_octet_start_number_master}/28",
                                                                  gw = "${var.gateway}",
                                                                  dns = "${var.dns_primary}",
                                                                  ssh_pub_key = "${file(var.ssh_pub_key)}"}))
    }
  }
}
