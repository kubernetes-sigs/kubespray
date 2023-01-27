terraform {
  required_version = ">= 1.0.0"
  required_providers {
    equinix = {
      source  = "equinix/equinix"
      version = ">=1.11.0"
    }
  }
}

# Configure the Equinix Metal Provider
provider "equinix" {
}
