output "master_ip" {
  value = local.master_ip
}

output "worker_ip" {
  value = local.worker_ip
}

output "bastion_ip" {
  value = local.bastion_ip
}

output "loadbalancer_domain" {
  value = {
    for key, loadbalancer in upcloud_loadbalancer.lb: key => {
      name = loadbalancer.name
      dns_name = loadbalancer.dns_name
      private = contains(loadbalancer.networks.*.type, "private")
      public = contains(loadbalancer.networks.*.type, "public")

    } if var.loadbalancer_enabled
  }
}
