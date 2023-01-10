variable "CLOUDFLARE_API_KEY" {
  type = string
  sensitive = true
}

variable "CLOUDFLARE_EMAIL" {
  type = string
  sensitive = true
}

variable "DOMAIN_NAME" {
  type = string
  sensitive = true
}

variable "VAULT_ADDRESS" {
  type = string
  sensitive = true
}

variable "VAULT_USERNAME" {
  type = string
  sensitive = true
}

variable "VAULT_PASSWORD" {
  type = string
  sensitive = true
}

variable "ID_RSA" {
  type = string
}

variable "ID_RSA_PUB" {
  type = string
}

variable "CA_KEY" {
  type = string
}

variable "CA_CERT" {
  type = string
}

variable "ADMIN_CONF" {
  type = string
}

variable "HOSTS_FILE" {
  type = string
}

variable "GIT_USERNAME" {
  type = string
  sensitive = true
}

variable "GIT_PASSWORD" {
  type = string
  sensitive = true
}

variable "STORAGE_HOSTNAME" {
  type = string
  sensitive = true
}

variable "STORAGE_MOUNT" {
  type = string
  sensitive = true
}

variable "MINIO_ACCESS_KEY" {
  type = string
  sensitive = true
}

variable "MINIO_SECRET_KEY" {
  type = string
  sensitive = true
}

locals {
  nodes = yamldecode(file(var.HOSTS_FILE)).all.hosts
  public_nodes = [for x in local.nodes: x if (!endswith(x.ip,x.wg_index))]
  storage_node = [for x in local.public_nodes: x if lookup(lookup(x,"node_labels",{}), "storage", false) != false][0]
}