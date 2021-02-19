prefix = "default"

inventory_file = "inventory.ini"

machines = {
  "master-0" : {
    "node_type" : "master",
    "ip" : "0.0.0.0/24"
  },
  "worker-0" : {
    "node_type" : "worker",
    "ip" : "0.0.0.0/24"
  },
  "worker-1" : {
    "node_type" : "worker",
    "ip" : "0.0.0.0/24"
  }
}
gateway = "0.0.0.0"
dns_primary = "8.8.4.4"
dns_secondary = "8.8.8.8"

ssh_pub_key = "~/.ssh/id_rsa.pub"

vsphere_datacenter = ""
vsphere_compute_cluster = "Cluster"
vsphere_datastore = "ssd-000000"
vsphere_server = "vsphere.server.com"
vsphere_hostname = "0.0.0.0"

template_name = "ubuntu-bionic-18.04-cloudimg"
