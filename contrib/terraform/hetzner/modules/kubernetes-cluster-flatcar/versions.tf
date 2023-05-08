terraform {
  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
    }
    ct = {
      source  = "poseidon/ct"
      version = "0.11.0"
    }
    null = {
      source = "hashicorp/null"
    }
  }
}
