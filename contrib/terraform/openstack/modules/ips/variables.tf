variable "number_of_k8s_controlplanes" {}

variable "number_of_k8s_controlplanes_no_etcd" {}

variable "number_of_k8s_nodes" {}

variable "floatingip_pool" {}

variable "number_of_bastions" {}

variable "external_net" {}

variable "network_name" {}

variable "router_id" {
  default = ""
}

variable "k8s_nodes" {}
