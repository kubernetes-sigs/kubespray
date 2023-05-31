output "control_plane_lb" {
  description = "The DNS name of LB for control plane"
  value       = nifcloud_load_balancer.this.dns_name
}

output "security_group_name" {
  description = "The security group used in the cluster"
  value = {
    bastion       = nifcloud_security_group.bn.group_name,
    control_plane = nifcloud_security_group.cp.group_name,
    worker        = nifcloud_security_group.wk.group_name,
  }
}

output "private_network_id" {
  description = "The private network used in the cluster"
  value       = nifcloud_private_lan.this.id
}

output "bastion_info" {
  description = "The basion information in cluster"
  value = { (nifcloud_instance.bn.instance_id) : {
    instance_id = nifcloud_instance.bn.instance_id,
    unique_id   = nifcloud_instance.bn.unique_id,
    private_ip  = nifcloud_instance.bn.private_ip,
    public_ip   = nifcloud_instance.bn.public_ip,
  } }
}

output "worker_info" {
  description = "The worker information in cluster"
  value = { for v in nifcloud_instance.wk : v.instance_id => {
    instance_id = v.instance_id,
    unique_id   = v.unique_id,
    private_ip  = v.private_ip,
    public_ip   = v.public_ip,
  } }
}

output "control_plane_info" {
  description = "The control plane information in cluster"
  value = { for v in nifcloud_instance.cp : v.instance_id => {
    instance_id = v.instance_id,
    unique_id   = v.unique_id,
    private_ip  = v.private_ip,
    public_ip   = v.public_ip,
  } }
}
