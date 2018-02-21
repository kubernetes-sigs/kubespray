variable "cluster_name" {
  default = "example"
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
  description = "Use 'nova flavor-list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_k8s_master" {
  description = "Use 'nova flavor-list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_k8s_node" {
  description = "Use 'nova flavor-list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_etcd" {
  description = "Use 'nova flavor-list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "flavor_gfs_node" {
  description = "Use 'nova flavor-list' command to see what your OpenStack instance uses for IDs"
  default     = 3
}

variable "network_name" {
  description = "name of the internal network to use"
  default     = "internal"
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

variable "external_net" {
  description = "uuid of the external/public network"
}
