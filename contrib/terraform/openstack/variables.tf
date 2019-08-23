variable "cluster_name" {
  default = "example"
}

variable "az_list" {
  description = "List of Availability Zones available in your OpenStack cluster"
  type        = "list"
  default     = ["nova"]
}

variable "number_of_bastions" {
  default = 1
}

variable "number_of_k8s_masters" {
  default = 2
}

variable "number_of_k8s_masters_no_etcd" {
  default = 2
}

variable "number_of_etcd" {
  default = 2
}

variable "number_of_k8s_masters_no_floating_ip" {
  default = 2
}

variable "number_of_k8s_masters_no_floating_ip_no_etcd" {
  default = 2
}

variable "number_of_k8s_nodes" {
  default = 1
}

variable "number_of_k8s_nodes_no_floating_ip" {
  default = 1
}

variable "number_of_gfs_nodes_no_floating_ip" {
  default = 0
}

variable "gfs_volume_size_in_gb" {
  default = 75
}

variable "public_key_path" {
  description = "The path of the ssh pub key"
  default     = "~/.ssh/id_rsa.pub"
}

variable "image" {
  description = "the image to use"
  default     = "ubuntu-14.04"
}

variable "image_gfs" {
  description = "Glance image to use for GlusterFS"
  default     = "ubuntu-16.04"
}

variable "ssh_user" {
  description = "used to fill out tags for ansible inventory"
  default     = "ubuntu"
}

variable "ssh_user_gfs" {
  description = "used to fill out tags for ansible inventory"
  default     = "ubuntu"
}

variable "flavor_bastion" {
  description = "Use 'openstack flavor list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_k8s_master" {
  description = "Use 'openstack flavor list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_k8s_node" {
  description = "Use 'openstack flavor list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_etcd" {
  description = "Use 'openstack flavor list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_gfs_node" {
  description = "Use 'openstack flavor list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "network_name" {
  description = "name of the internal network to use"
  default     = "internal"
}

variable "network_dns_domain" {
  description = "dns_domain for the internal network"
  type        = "string"
  default     = null
}

variable "use_neutron" {
  description = "Use neutron"
  default     = 1
}

variable "subnet_cidr" {
  description = "Subnet CIDR block."
  type        = "string"
  default     = "10.0.0.0/24"
}

variable "dns_nameservers" {
  description = "An array of DNS name server names used by hosts in this subnet."
  type        = "list"
  default     = []
}

variable "floatingip_pool" {
  description = "name of the floating ip pool to use"
  default     = "external"
}

variable "wait_for_floatingip" {
  description = "Terraform will poll the instance until the floating IP has been associated."
  default     = "false"
}

variable "external_net" {
  description = "uuid of the external/public network"
}

variable "supplementary_master_groups" {
  description = "supplementary kubespray ansible groups for masters, such kube-node"
  default     = ""
}

variable "supplementary_node_groups" {
  description = "supplementary kubespray ansible groups for worker nodes, such as kube-ingress"
  default     = ""
}

variable "bastion_allowed_remote_ips" {
  description = "An array of CIDRs allowed to SSH to hosts"
  type        = "list"
  default     = ["0.0.0.0/0"]
}

variable "master_allowed_remote_ips" {
  description = "An array of CIDRs allowed to access API of masters"
  type        = "list"
  default     = ["0.0.0.0/0"]
}

variable "k8s_allowed_remote_ips" {
  description = "An array of CIDRs allowed to SSH to hosts"
  type        = "list"
  default     = []
}

variable "k8s_allowed_egress_ips" {
  description = "An array of CIDRs allowed for egress traffic"
  type        = "list"
  default     = ["0.0.0.0/0"]
}

variable "worker_allowed_ports" {
  type = "list"

  default = [
    {
      "protocol"         = "tcp"
      "port_range_min"   = 30000
      "port_range_max"   = 32767
      "remote_ip_prefix" = "0.0.0.0/0"
    },
  ]
}
