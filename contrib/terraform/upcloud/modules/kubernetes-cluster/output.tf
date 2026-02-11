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
    for key, loadbalancer in upcloud_loadbalancer.lb : key => {
      name     = loadbalancer.name
      dns_name = loadbalancer.dns_name
      private  = contains(loadbalancer.networks.*.type, "private")
      public   = contains(loadbalancer.networks.*.type, "public")

    } if var.loadbalancer_enabled
  }
}

output "loadbalancer_dns_names" {
  description = "DNS names for load balancers"
  value = {
    for k, v in upcloud_loadbalancer.lb :
    k => v.dns_name
  }
}

output "loadbalancer_floating_ips" {
  description = "Stable public IP addresses of load balancers for customer whitelisting"
  value = {
    for k, lb in upcloud_loadbalancer.lb :
    k => {
      dns_name = lb.dns_name
      ips      = flatten([for network in lb.nodes[0].networks : network.ip_addresses[*].address if network.type == "public"])
    }
  }
}