terraform {
  required_providers {
    opennebula = {
      source  = "OpenNebula/opennebula"
      version = "~> 1.5"
    }
  }
  required_version = ">= 1.3.0"
}
