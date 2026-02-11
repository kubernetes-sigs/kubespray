terraform {
  required_providers {
    upcloud = {
      source  = "UpCloudLtd/upcloud"
      version = "~> 5.25.0"
    }
  }
  required_version = ">= 0.13"
}