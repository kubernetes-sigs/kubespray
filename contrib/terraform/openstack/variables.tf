variable "cluster_name" {
  default = "example"
}

variable "az_list" {
  description = "List of Availability Zones to use for masters in your OpenStack cluster"
  type        = list(string)
  default     = ["nova"]
}

variable "az_list_node" {
  description = "List of Availability Zones to use for nodes in your OpenStack cluster"
  type        = list(string)
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

variable "bastion_root_volume_size_in_gb" {
  default = 0
}

variable "etcd_root_volume_size_in_gb" {
  default = 0
}

variable "master_root_volume_size_in_gb" {
  default = 0
}

variable "node_root_volume_size_in_gb" {
  default = 0
}

variable "gfs_root_volume_size_in_gb" {
  default = 0
}

variable "gfs_volume_size_in_gb" {
  default = 75
}

variable "master_volume_type" {
  default = "Default"
}

variable "public_key_path" {
  description = "The path of the ssh pub key"
  default     = "~/.ssh/id_rsa.pub"
}

variable "image" {
  description = "the image to use"
  default     = ""
}

variable "image_gfs" {
  description = "Glance image to use for GlusterFS"
  default     = ""
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
  type        = string
  default     = null
}

variable "use_neutron" {
  description = "Use neutron"
  default     = 1
}

variable "subnet_cidr" {
  description = "Subnet CIDR block."
  type        = string
  default     = "10.0.0.0/24"
}

variable "dns_nameservers" {
  description = "An array of DNS name server names used by hosts in this subnet."
  type        = list(string)
  default     = []
}

variable "k8s_master_fips" {
  description = "specific pre-existing floating IPs to use for master nodes"
  type        = list(string)
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
  description = "supplementary kubespray ansible groups for masters, such kube_node"
  default     = ""
}

variable "supplementary_node_groups" {
  description = "supplementary kubespray ansible groups for worker nodes, such as kube_ingress"
  default     = ""
}

variable "bastion_allowed_remote_ips" {
  description = "An array of CIDRs allowed to SSH to hosts"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "master_allowed_remote_ips" {
  description = "An array of CIDRs allowed to access API of masters"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "k8s_allowed_remote_ips" {
  description = "An array of CIDRs allowed to SSH to hosts"
  type        = list(string)
  default     = []
}

variable "k8s_allowed_egress_ips" {
  description = "An array of CIDRs allowed for egress traffic"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "master_allowed_ports" {
  type = list(any)

  default = []
}

variable "worker_allowed_ports" {
  type = list(any)

  default = [
    {
      "protocol"         = "tcp"
      "port_range_min"   = 30000
      "port_range_max"   = 32767
      "remote_ip_prefix" = "0.0.0.0/0"
    },
  ]
}

variable "use_access_ip" {
  default = 1
}

variable "use_server_groups" {
  default = false
}

variable "router_id" {
  description = "uuid of an externally defined router to use"
  default     = null
}

variable "router_internal_port_id" {
  description = "uuid of the port connection our router to our network"
  default     = null
}

variable "k8s_nodes" {
  default = {}
}

variable "extra_sec_groups" {
  default = false
}

variable "extra_sec_groups_name" {
  default = "custom"
}

variable "image_uuid" {
  description = "uuid of image inside openstack to use"
  default     = ""
}

variable "image_gfs_uuid" {
  description = "uuid of image to be used on gluster fs nodes. If empty defaults to image_uuid"
  default     = ""
}

variable "image_master" {
  description = "uuid of image inside openstack to use"
  default     = ""
}

variable "image_master_uuid" {
  description = "uuid of image to be used on master nodes. If empty defaults to image_uuid"
  default     = ""
}

variable "group_vars_path" {
  description = "path to the inventory group vars directory"
  type        = string
  default     = "./group_vars"
}
