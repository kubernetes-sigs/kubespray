# your Kubernetes cluster name here
cluster_name = "i-didnt-read-the-docs"

# list of availability zones available in your OpenStack cluster
#az_list = ["nova"]

# SSH key to use for access to nodes
public_key_path = "~/.ssh/id_rsa.pub"

# image to use for bastion, masters, standalone etcd instances, and nodes
image = "<image name>"

# user on the node (ex. core on Container Linux, ubuntu on Ubuntu, etc.)
ssh_user = "<cloud-provisioned user>"

# 0|1 bastion nodes
number_of_bastions = 0

#flavor_bastion = "<UUID>"

# standalone etcds
number_of_etcd = 0

# masters
number_of_k8s_masters = 1

number_of_k8s_masters_no_etcd = 0

number_of_k8s_masters_no_floating_ip = 0

number_of_k8s_masters_no_floating_ip_no_etcd = 0

flavor_k8s_master = "<UUID>"

k8s_masters = {
  # "master-1" = {
  #   "az"          = "nova"
  #   "flavor"      = "<UUID>"
  #   "floating_ip" = true
  #   "etcd" = true
  # },
  # "master-2" = {
  #   "az"          = "nova"
  #   "flavor"      = "<UUID>"
  #   "floating_ip" = false
  #   "etcd" = true
  # },
  # "master-3" = {
  #   "az"          = "nova"
  #   "flavor"      = "<UUID>"
  #   "floating_ip" = true
  #   "etcd" = true
  # },
}


# nodes
number_of_k8s_nodes = 2

number_of_k8s_nodes_no_floating_ip = 4

#flavor_k8s_node = "<UUID>"

# GlusterFS
# either 0 or more than one
#number_of_gfs_nodes_no_floating_ip = 0
#gfs_volume_size_in_gb = 150
# Container Linux does not support GlusterFS
#image_gfs = "<image name>"
# May be different from other nodes
#ssh_user_gfs = "ubuntu"
#flavor_gfs_node = "<UUID>"

# networking
network_name = "<network>"

# Use a existing network with the name of network_name. Set to false to create a network with name of network_name.
# use_existing_network = true

external_net = "<UUID>"

subnet_cidr = "<cidr>"

floatingip_pool = "<pool>"

bastion_allowed_remote_ips = ["0.0.0.0/0"]

# Force port security to be null. Some cloud providers do not allow to set port security.
# force_null_port_security = false
