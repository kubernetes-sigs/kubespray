output "templa" {
    value = "${google_compute_region_instance_group_manager.instance_group_manager.self_link}"
}

output "group_name" {
    value = "${var.env_name}-${var.template_name}"
}

output "ans_ssh_name" {
    value ="${data.google_compute_region_instance_group.group.instances.*.instance[0]}"
}

output "instance_details" {
    value ="${data.google_compute_region_instance_group.group.instances.*.instance}"
}