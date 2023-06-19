region = "jp-west-1"
az     = "west-11"

instance_key_name = "deployerkey"

instance_type_bn = "e-medium"
instance_type_cp = "e-medium"
instance_type_wk = "e-medium"

private_network_cidr = "192.168.30.0/24"
instances_cp = {
  "cp01" : { private_ip : "192.168.30.11/24" }
  "cp02" : { private_ip : "192.168.30.12/24" }
  "cp03" : { private_ip : "192.168.30.13/24" }
}
instances_wk = {
  "wk01" : { private_ip : "192.168.30.21/24" }
  "wk02" : { private_ip : "192.168.30.22/24" }
}
private_ip_bn = "192.168.30.10/24"

image_name = "Ubuntu Server 22.04 LTS"
