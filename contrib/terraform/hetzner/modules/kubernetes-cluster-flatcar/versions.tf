terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
    }
    ct = {
      source  = "poseidon/ct"
    }
    null = {
      source  = "hashicorp/null"
    }
  }
}
