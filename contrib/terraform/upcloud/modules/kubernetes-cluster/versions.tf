
terraform {
  required_providers {
    upcloud = {
      source = "UpCloudLtd/upcloud"
      version = "~>2.7.1"
    }
  }
  required_version = ">= 0.13"
}
