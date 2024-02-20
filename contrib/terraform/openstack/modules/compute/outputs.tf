output "k8s_master_ips" {
  value = concat(openstack_compute_instance_v2.k8s_master_no_floating_ip.*, openstack_compute_instance_v2.k8s_master_no_floating_ip_no_etcd.*)
}
