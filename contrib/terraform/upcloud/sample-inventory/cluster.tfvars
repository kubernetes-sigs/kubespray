# See: https://developers.upcloud.com/1.3/5-zones/
zone     = "fi-hel1"
username = "ubuntu"

inventory_file = "inventory.ini"

#  A valid domain name, e.g. host.example.com. The maximum length is 128 characters.
hostname = "example.com"

#  Set the operating system using UUID or exact name
template_name = "Ubuntu Server 20.04 LTS (Focal Fossa)"
ssh_public_keys = [
  # Put your public SSH key here
  "ssh-rsa I-did-not-read-the-docs",
  "ssh-rsa I-did-not-read-the-docs 2",
]

check list of available plan https://developers.upcloud.com/1.3/7-plans/
machines = {
  "master-0" : {
    "node_type" : "master",
    #number of cpu cores
    "cpu" : "2",
    #memory size in MB
    "mem" : "4096"
    # The size of the storage in GB
    "disk_size" : 250
  },
  "worker-0" : {
    "node_type" : "worker",
    #number of cpu cores
    "cpu" : "2",
    #memory size in MB
    "mem" : "4096"
    # The size of the storage in GB
    "disk_size" : 250
  },
  "worker-1" : {
    "node_type" : "worker",
    #number of cpu cores
    "cpu" : "2",
    #memory size in MB
    "mem" : "4096"
    # The size of the storage in GB
    "disk_size" : 250
  },
  "worker-2" : {
    "node_type" : "worker",
    #number of cpu cores
    "cpu" : "2",
    #memory size in MB
    "mem" : "4096"
    # The size of the storage in GB
    "disk_size" : 250
  }
}
