
terraform {
  required_providers {
    upcloud = {
      source  = "UpCloudLtd/upcloud"
      version = "~>5.29.1"
    }
  }
  required_version = ">= 0.13"
}
