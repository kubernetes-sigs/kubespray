terraform {
  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
    }
  }
  experiments = [module_variable_optional_attrs]
  required_version = ">= 0.14.0"
}
