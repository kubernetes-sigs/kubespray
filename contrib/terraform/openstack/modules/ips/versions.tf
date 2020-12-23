terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
    openstack = {
      source = "terraform-provider-openstack/openstack"
    }
  }
  required_version = ">= 0.12.26"
}
