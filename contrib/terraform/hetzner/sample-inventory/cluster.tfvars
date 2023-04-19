prefix         = "default"
zone           = "hel1"
network_zone   = "eu-central"
inventory_file = "inventory.ini"

ssh_public_keys = [
  # Put your public SSH key here
  "ssh-rsa I-did-not-read-the-docs",
  "ssh-rsa I-did-not-read-the-docs 2",
]

ssh_private_key_path = "~/.ssh/id_rsa"

machines = {
  "master-0" : {
    "node_type" : "master",
    "size" : "cx21",
    "image" : "ubuntu-22.04",
  },
  "worker-0" : {
    "node_type" : "worker",
    "size" : "cx21",
    "image" : "ubuntu-22.04",
  },
  "worker-1" : {
    "node_type" : "worker",
    "size" : "cx21",
    "image" : "ubuntu-22.04",
  }
}

nodeport_whitelist = [
  "0.0.0.0/0"
]

ingress_whitelist = [
  "0.0.0.0/0"
]

ssh_whitelist = [
  "0.0.0.0/0"
]

api_server_whitelist = [
  "0.0.0.0/0"
]
