output "k8s_masters" {
  value = "${packet_device.k8s_master.*.access_public_ipv4}"
}

output "k8s_masters_no_etc" {
  value = "${packet_device.k8s_master_no_etcd.*.access_public_ipv4}"
}

output "k8s_etcds" {
  value = "${packet_device.k8s_etcd.*.access_public_ipv4}"
}

output "k8s_nodes" {
  value = "${packet_device.k8s_node.*.access_public_ipv4}"
}
