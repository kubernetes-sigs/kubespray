variable "zone" {
  type = string
}

variable "hostname"{
 default ="example.com"
}

variable "template_name"{}

variable "username"{}

variable "machines" {
  description = "Cluster machines"
  type = map(object({
    node_type = string
    cpu      = string
    mem      = string
    disk_size =  number
  }))
}

variable "ssh_public_keys" {
  type = list(string)
}
