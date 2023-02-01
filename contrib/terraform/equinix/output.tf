output "k8s_masters" {
  value = equinix_metal_device.k8s_master.*.access_public_ipv4
}

output "k8s_masters_no_etc" {
  value = equinix_metal_device.k8s_master_no_etcd.*.access_public_ipv4
}

output "k8s_etcds" {
  value = equinix_metal_device.k8s_etcd.*.access_public_ipv4
}

output "k8s_nodes" {
  value = equinix_metal_device.k8s_node.*.access_public_ipv4
}
