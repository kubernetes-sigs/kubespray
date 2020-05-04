variable "env_name" {
  description = "Environment Name"
  default = "dev"
}

variable "gcp_project_id" {
  description = "project_id name"
  default = ""
}

variable "template_name"{
    description = "Template Name"
    default = "terraform-template"
}
variable "region" {
  description = "Region details"
  default =""
}

variable "machine_type"{
    description = "Machine type for the instance"
    default = "n1-standard-1"
}

variable "source_image" {
  description = "Image ID for the instance"
  default = "centos7"
}

variable "disk_size_gb" {
  description = "Total Disk size"
  default = "100"
}

variable "disk_type" {
  
  description = "Type of the disk"
  default = "pd-standard"
}

variable "network_interface" {
  description = "Template Network interface"
  default = ""
}

variable "subnetwork" {
  description = "Template subnetwork"
  default = ""
}
variable "mode" {
  description = "Template mode"
  default = "READ_WRITE"
}

variable "svca_email" {
  description = "Service account email"
  default = ""
}

variable "svca_scopes" {
  description = "Service account scope" 
  default = ["https://www.googleapis.com/auth/cloud-platform"]
}

############## Instance group related variables ######################


variable "compute_zone" {
  default = "us-central1-a"
  description = "Zone where instance will be created"
}

variable "target_size" {
  default = "1"
  description = "Total Number of Instances in the group manager"
}

variable "component" {
  default = "default"
}
