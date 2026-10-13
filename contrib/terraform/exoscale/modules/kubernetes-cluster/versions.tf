terraform {
  required_providers {
    exoscale = {
      source  = "exoscale/exoscale"
      version = ">= 0.21, < 0.75"
    }
  }
  required_version = ">= 0.13"
}
