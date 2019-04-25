# your Kubernetes cluster name here
cluster_name = "mycluster"

# Your Packet project ID. See https://support.packet.com/kb/articles/api-integrations
packet_project_id = "Example-API-Token"

# The public SSH key to be uploaded into authorized_keys in bare metal Packet nodes provisioned
# leave this value blank if the public key is already setup in the Packet project
# Terraform will complain if the public key is setup in Packet
public_key_path = "~/.ssh/id_rsa.pub"

# cluster location
facility = "ewr1"

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
