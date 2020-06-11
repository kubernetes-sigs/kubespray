output "k8s_controlplanes" {
  value = packet_device.k8s_controlplane.*.access_public_ipv4
}

output "k8s_controlplanes_no_etc" {
  value = packet_device.k8s_controlplane_no_etcd.*.access_public_ipv4
}

output "k8s_etcds" {
  value = packet_device.k8s_etcd.*.access_public_ipv4
}

output "k8s_nodes" {
  value = packet_device.k8s_node.*.access_public_ipv4
}

