variable "region" {
  description = "OCI region for the CI cluster and artifact bucket."
  type        = string
}

variable "compartment_id" {
  description = "OCID of the compartment containing the CI resources."
  type        = string
}

variable "availability_domain" {
  description = "Availability domain with capacity for the chosen bare metal shape."
  type        = string
}

variable "kubernetes_version" {
  description = "OKE version to deploy (v1.29 or later is required for dual stack)."
  type        = string
}

variable "node_image_id" {
  description = "OCID of an OKE image for the selected Kubernetes version, shape, and region (build 754 or later)."
  type        = string
}

variable "node_shape" {
  description = "OKE supported bare metal shape available in the selected availability domain."
  type        = string
  default     = "BM.Standard.E4.128"

  validation {
    condition     = startswith(var.node_shape, "BM.")
    error_message = "The CI node shape must be a bare metal shape."
  }
}

variable "cluster_name" {
  description = "Name of the OKE cluster and prefix for OCI resources."
  type        = string
  default     = "kubespray-ci"
}

variable "artifact_bucket_name" {
  description = "Name for the private OCI Object Storage bucket replacing MinIO."
  type        = string
}

variable "on_demand_nodes" {
  description = "Additional bare metal workers to provision on demand, from zero through four."
  type        = number
  default     = 0

  validation {
    condition     = var.on_demand_nodes >= 0 && var.on_demand_nodes <= 4 && floor(var.on_demand_nodes) == var.on_demand_nodes
    error_message = "on_demand_nodes must be an integer from zero to four."
  }
}

variable "api_allowed_ipv4_cidrs" {
  description = "IPv4 networks allowed to reach the public Kubernetes API endpoint."
  type        = list(string)
  default     = []
}

variable "api_allowed_ipv6_cidrs" {
  description = "IPv6 networks allowed to reach the public Kubernetes API endpoint."
  type        = list(string)
  default     = []
}
