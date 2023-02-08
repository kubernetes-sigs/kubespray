# your Kubernetes cluster name here
cluster_name = "mycluster"

# Your Equinix Metal project ID. See https://metal.equinix.com/developers/docs/accounts/
equinix_metal_project_id = "Example-Project-Id"

# The public SSH key to be uploaded into authorized_keys in bare metal Equinix Metal nodes provisioned
# leave this value blank if the public key is already setup in the Equinix Metal project
# Terraform will complain if the public key is setup in Equinix Metal
public_key_path = "~/.ssh/id_rsa.pub"

# cluster location
facility = "ewr1"

# operating_system
operating_system = "ubuntu_22_04"

# standalone etcds
number_of_etcd = 0

plan_etcd = "t1.small.x86"

# masters
number_of_k8s_masters = 1

number_of_k8s_masters_no_etcd = 0

plan_k8s_masters = "t1.small.x86"

plan_k8s_masters_no_etcd = "t1.small.x86"

# nodes
number_of_k8s_nodes = 2

plan_k8s_nodes = "t1.small.x86"
