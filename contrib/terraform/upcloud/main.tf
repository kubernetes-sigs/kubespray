
terraform {
  required_version = ">= 0.13.0"
}
provider "upcloud" {
  # Your UpCloud credentials are read from  environment variables:
  username = var.UPCLOUD_USERNAME
  password = var.UPCLOUD_PASSWORD
}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"

  prefix = var.prefix
  zone   = var.zone

  template_name = var.template_name
  username      = var.username

  private_network_cidr = var.private_network_cidr

  machines = var.machines

  ssh_public_keys = var.ssh_public_keys
}

#
# Generate ansible inventory
#

data "template_file" "inventory" {
  template = file("${path.module}/templates/inventory.tpl")

  vars = {
    connection_strings_master = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s ip=%s etcd_member_name=etcd%d",
      keys(module.kubernetes.master_ip),
      values(module.kubernetes.master_ip).*.public_ip,
      values(module.kubernetes.master_ip).*.private_ip,
    range(1, length(module.kubernetes.master_ip) + 1)))
    connection_strings_worker = join("\n", formatlist("%s ansible_user=ubuntu ansible_host=%s ip=%s",
      keys(module.kubernetes.worker_ip),
      values(module.kubernetes.worker_ip).*.public_ip,
    values(module.kubernetes.worker_ip).*.private_ip))
    list_master = join("\n", formatlist("%s",
    keys(module.kubernetes.master_ip)))
    list_worker = join("\n", formatlist("%s",
    keys(module.kubernetes.worker_ip)))
  }
}

resource "null_resource" "inventories" {
  provisioner "local-exec" {
    command = "echo '${data.template_file.inventory.rendered}' > ${var.inventory_file}"
  }

  triggers = {
    template = data.template_file.inventory.rendered
  }
}
