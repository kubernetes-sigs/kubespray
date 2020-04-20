data "google_compute_image" "image_selflink"{
  name = "${var.source_image}"
  project = "${var.gcp_project_id}"
}

resource "google_compute_instance_template" "ansible_template" {
  name        = var.template_name
  description = "Kube ${var.component} template for Environment ${var.env_name}"

  tags = []

  labels = {}
  instance_description = "This template is created by terraform"
  machine_type         = var.machine_type
  can_ip_forward       = true
  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
  }

  disk {
    source_image = data.google_compute_image.image_selflink.self_link
    auto_delete  = true
    boot         = true
    type         = "PERSISTENT"
    disk_size_gb = var.disk_size_gb
    disk_type     = var.disk_type
    device_name = var.template_name
    mode         = "READ_WRITE"
  }
  network_interface {
    network = var.network_interface
    subnetwork = var.subnetwork
  }
 
  metadata = {
    foo = "bar"
  }

  service_account {
    email = var.svca_email
    scopes = var.svca_scopes
  }
}


resource "google_compute_region_instance_group_manager" "instance_group_manager" {
  depends_on = [google_compute_instance_template.ansible_template]
  version {
       instance_template = google_compute_instance_template.ansible_template.self_link
  }
  name = var.template_name
  base_instance_name = var.template_name
  region = var.region
  #zone               = var.compute_zone
  target_size        = var.target_size
}


resource "null_resource" "a_wait" {
  depends_on = [google_compute_region_instance_group_manager.instance_group_manager]
  provisioner "local-exec" {
      command = "ping 127.0.0.1 -c 100" #or sleep 10
  }
}
data "google_compute_region_instance_group" "group" {
    depends_on = [null_resource.a_wait]
    name = var.template_name
}


resource "null_resource" "create_inv_file" {
  #depends_on = [google_compute_region_instance_group.group]
  depends_on = [null_resource.a_wait]
  count = var.target_size
  provisioner "local-exec" {
    command = " echo ${var.env_name},${var.component},${data.google_compute_region_instance_group.group.instances.*.instance[count.index]} >> ${var.env_name}-inventory.ini"
  }
}
