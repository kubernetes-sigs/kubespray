prefix = "default"
zone   = "ch-gva-2"

inventory_file = "inventory.ini"

ssh_public_keys = [
  # Put your public SSH key here
  "ssh-rsa I-did-not-read-the-docs",
  "ssh-rsa I-did-not-read-the-docs 2",
]

machines = {
  "master-0" : {
    "node_type" : "master",
    "size" : "Small",
    "boot_disk" : {
      "image_name" : "Linux Ubuntu 20.04 LTS 64-bit",
      "root_partition_size" : 50,
      "node_local_partition_size" : 0,
      "ceph_partition_size" : 0
    }
  },
  "worker-0" : {
    "node_type" : "worker",
    "size" : "Large",
    "boot_disk" : {
      "image_name" : "Linux Ubuntu 20.04 LTS 64-bit",
      "root_partition_size" : 50,
      "node_local_partition_size" : 0,
      "ceph_partition_size" : 0
    }
  },
  "worker-1" : {
    "node_type" : "worker",
    "size" : "Large",
    "boot_disk" : {
      "image_name" : "Linux Ubuntu 20.04 LTS 64-bit",
      "root_partition_size" : 50,
      "node_local_partition_size" : 0,
      "ceph_partition_size" : 0
    }
  },
  "worker-2" : {
    "node_type" : "worker",
    "size" : "Large",
    "boot_disk" : {
      "image_name" : "Linux Ubuntu 20.04 LTS 64-bit",
      "root_partition_size" : 50,
      "node_local_partition_size" : 0,
      "ceph_partition_size" : 0
    }
  }
}

nodeport_whitelist = [
  "0.0.0.0/0"
]

ssh_whitelist = [
  "0.0.0.0/0"
]

api_server_whitelist = [
  "0.0.0.0/0"
]
