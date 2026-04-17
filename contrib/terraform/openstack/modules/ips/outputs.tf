locals {
  k8s_masters_reserved_fips = {
    for key, value in var.k8s_masters : key => {
      address = value.reserved_floating_ip
    } if value.floating_ip && (lookup(value, "reserved_floating_ip", "") != "")
  }
  k8s_masters_create_fips = {
    for key, value in openstack_networking_floatingip_v2.k8s_masters : key => {
      address = value.address
    }
  }
  k8s_nodes_reserved_fips = {
    for key, value in var.k8s_nodes : key => {
      address = value.reserved_floating_ip
    } if value.floating_ip && (lookup(value, "reserved_floating_ip", "") != "")
  }
  k8s_nodes_create_fips = {
    for key, value in openstack_networking_floatingip_v2.k8s_nodes : key => {
      address = value.address
    }
  }
}

# If k8s_master_fips is already defined as input, keep the same value since new FIPs have not been created.
output "k8s_master_fips" {
  value = length(var.k8s_master_fips) > 0 ? var.k8s_master_fips : openstack_networking_floatingip_v2.k8s_master[*].address
}

output "k8s_masters_fips" {
  value = merge(local.k8s_masters_create_fips, local.k8s_masters_reserved_fips)
}

# If k8s_master_fips is already defined as input, keep the same value since new FIPs have not been created.
output "k8s_master_no_etcd_fips" {
  value = length(var.k8s_master_fips) > 0 ? var.k8s_master_fips : openstack_networking_floatingip_v2.k8s_master_no_etcd[*].address
}

output "k8s_node_fips" {
  value = openstack_networking_floatingip_v2.k8s_node[*].address
}

output "k8s_nodes_fips" {
  value = merge(local.k8s_nodes_create_fips, local.k8s_nodes_reserved_fips)
}

output "bastion_fips" {
  value = length(var.bastion_fips) > 0 ? var.bastion_fips : openstack_networking_floatingip_v2.bastion[*].address
}
