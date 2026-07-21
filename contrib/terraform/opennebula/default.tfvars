prefix = "k8s"

# Prefer an absolute path (relative paths resolve against the module directory):
# inventory_file = "/path/to/inventory/mycluster/inventory.ini"

# Existing OpenNebula objects
template_name = "i-did-not-read-the-docs" # e.g. ubuntu2404-context
network_name  = "i-did-not-read-the-docs" # e.g. private

# Node counts (nodes are named master-0.., worker-0..)
master_count = 1
worker_count = 2

# Advanced alternative: named nodes and/or static IPs. Takes precedence over
# master_count/worker_count when set.
# machines = {
#   "master-0" : {
#     "node_type" : "master",
#     "ip" : "" # optional static IP from an address range of the network, e.g. 192.168.0.10
#   },
#   "worker-0" : {
#     "node_type" : "worker",
#     "ip" : ""
#   }
# }

ssh_public_keys = [
  # Put your public SSH key here
  "ssh-rsa I-did-not-read-the-docs",
]

# SSH user for the generated inventory (one-context installs keys for root
# on standard OpenNebula marketplace images)
# ansible_user = "root"

## Sizing
# master_vcpu      = 2
# master_memory    = 4096
# worker_vcpu      = 4
# worker_memory    = 8192
# master_disk_size = 0 # MB; 0 keeps the template disk size
# worker_disk_size = 0 # MB; 0 keeps the template disk size

## OpenNebula extras
# additional_disk_size     = 0  # MB; extra DATABLOCK disk on every node
# image_datastore_name     = "" # required when additional_disk_size > 0
# masters_anti_affinity    = false
# network_reservation_size = 0  # carve an address reservation out of network_name
# network_reservation_first_ip = "" # pin the reserved range's first IP
# network_reservation_ar_id    = null # parent address-range ID to reserve from (null = provider default)
