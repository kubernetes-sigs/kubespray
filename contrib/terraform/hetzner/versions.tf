terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "1.38.2"
    }
    null = {
      source = "hashicorp/null"
    }
  }
  required_version = ">= 0.14"
}
