# your Kubernetes cluster name here
cluster_name = "mycluster"

# Your Packet project ID. See https://support.packet.com/kb/articles/api-integrations
packet_project_id = "Example-API-Token"

# SSH key to use for access to nodes, "" to skip
public_key_path = "~/.ssh/id_rsa.pub"

# standalone etcds
number_of_etcd = 0

# masters
number_of_k8s_masters = 1
number_of_k8s_masters_no_etcd = 0

# nodes
number_of_k8s_nodes = 2
