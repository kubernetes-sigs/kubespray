variable "availability_zone" {
  description = "The availability zone"
  type        = string
}

variable "prefix" {
  description = "The prefix for the entire cluster"
  type        = string
  validation {
    condition     = length(var.prefix) <= 5
    error_message = "Must be a less than 5 character long."
  }
}

variable "private_network_cidr" {
  description = "The subnet of private network"
  type        = string
  validation {
    condition     = can(cidrnetmask(var.private_network_cidr))
    error_message = "Must be a valid IPv4 CIDR block address."
  }
}

variable "private_ip_bn" {
  description = "Private IP of bastion server"
  type        = string
}

variable "instances_cp" {
  type = map(object({
    private_ip = string
  }))
}

variable "instances_wk" {
  type = map(object({
    private_ip = string
  }))
}

variable "instance_key_name" {
  description = "The key name of the Key Pair to use for the instance"
  type        = string
}

variable "instance_type_bn" {
  description = "The instance type of bastion server"
  type        = string
}

variable "instance_type_wk" {
  description = "The instance type of worker"
  type        = string
}

variable "instance_type_cp" {
  description = "The instance type of control plane"
  type        = string
}

variable "image_name" {
  description = "The name of image"
  type        = string
}

variable "additional_lb_filter" {
  description = "Additional LB filter"
  type        = list(string)
}

variable "accounting_type" {
  type    = string
  default = "1"
  validation {
    condition = anytrue([
      var.accounting_type == "1", // Monthly
      var.accounting_type == "2", // Pay per use
    ])
    error_message = "Must be a 1 or 2."
  }
}
