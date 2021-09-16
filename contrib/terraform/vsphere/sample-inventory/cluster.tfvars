prefix = "default"

inventory_file = "inventory.ini"

machines = {
  "master-0" : {
    "node_type" : "master",
    "ip" : "i-did-not-read-the-docs" # e.g. 192.168.0.2/24
  },
  "worker-0" : {
    "node_type" : "worker",
    "ip" : "i-did-not-read-the-docs" # e.g. 192.168.0.2/24
  },
  "worker-1" : {
    "node_type" : "worker",
    "ip" : "i-did-not-read-the-docs" # e.g. 192.168.0.2/24
  }
}

gateway = "i-did-not-read-the-docs" # e.g. 192.168.0.2

ssh_public_keys = [
  # Put your public SSH key here
  "ssh-rsa I-did-not-read-the-docs",
  "ssh-rsa I-did-not-read-the-docs 2",
]

vsphere_datacenter      = "i-did-not-read-the-docs"
vsphere_compute_cluster = "i-did-not-read-the-docs" # e.g. Cluster
vsphere_datastore       = "i-did-not-read-the-docs" # e.g. ssd-000000
vsphere_server          = "i-did-not-read-the-docs" # e.g. vsphere.server.com
vsphere_hostname        = "i-did-not-read-the-docs" # e.g. 192.168.0.2

template_name = "i-did-not-read-the-docs" # e.g. ubuntu-bionic-18.04-cloudimg
