terraform {
  required_version = ">= 1.0.0"

  provider_meta "equinix" {
    module_name = "kubespray"
  }
  required_providers {
    equinix = {
      source  = "equinix/equinix"
      version = "1.24.0"
    }
  }
}

# Configure the Equinix Metal Provider
provider "equinix" {
}
