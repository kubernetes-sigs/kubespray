terraform {
  required_providers {
    vsphere = {
      source  = "hashicorp/vsphere"
      version = ">= 1.24.3"
    }
  }
  required_version = ">= 0.13"
}
