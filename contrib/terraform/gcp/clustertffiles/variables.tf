
variable "user_name" {
  description = "User Name"
  default = "app"
}

################################### Variable Section #########################

variable "region" {
  description = "Region details"
  default     = "us-central1"
}

variable "env" {
  description = "Environment Details or cluster name- dev,stage,test,prod,etc"
  default     = "test"
}

variable "kube_automation_folder" {
  description = "Folder location in the ansible machine where kube configurations are stored"
  default     = "/home/app/kube_automation"
}

variable "kubespray_repo_url" {
  description = "Kubespray repo URL hosted  in the github (Note: HTTPS url to be copied with credentails)"
  default = "https://github.com/kubernetes-sigs/kubespray.git"
}


variable "gcp_project_id" {
  description = "GCP project_id  name"
  default = ""
}

# TF-UPGRADE-TODO: Block type was not recognized, so this block and its contents were not automatically upgraded.

######################## Kube Master Node Details  #############
variable "kube_master_machine_type" {
  description = "Machine Type, if not provided by default n1-standard-1 will be considered"
  default = "n1-standard-1"
}

variable "kube_master_source_image" {
  description = "OS image name"
  default = "centos-6-v20190729"
}

variable "kube_master_disk_size_gb" {
  description = "Total disk size allocated, by default 100GB"
  default="100"
}

variable "kube_master_disk_type" {
  description = "Disk type, pd-standard or pd-ssd"
  default = "pd-standard"
}

variable "kube_master_network_interface" {
  description = "Network Interface details"
  default = ""
}

variable "kube_master_subnetwork" {
  description = "Subnetwork details"
  default = ""
}

variable "kube_master_mode" {
  description = "Instance Mode"
  default = "READ_WRITE"
}

variable "kube_master_svca_email" {
  description = "Service Account Email"
  default = ""
}

variable "kube_master_svca_scopes" {
  description = "Service Account Scope"
  default = ["https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring.write","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"]
}

variable kube_master_target_size {
  description = "Number of kubernetes masters"
  default = 2
}


############### ETCD node 
variable "kube_etcd_machine_type" {
  description = "etcd Machine Type, if not provided by default n1-standard-1 will be considered"
  default = "n1-standard-1"
}

variable "kube_etcd_source_image" {
  description = "OS image name"
  default = "centos-6-v20190729"
}

variable "kube_etcd_disk_size_gb" {
  description = "Disk size, by default 100GB"
  default="100"
}

variable "kube_etcd_disk_type" {
  description = "Disk type, pd-standard or pd-ssd"
  default="pd-standard"
}

variable "kube_etcd_network_interface" {
  description = "Network interface details"
  default = ""
}

variable "kube_etcd_subnetwork" {
  description = "Subnetwork details"
  default = ""
}

variable "kube_etcd_mode" {
  description = "Instance Mode"
  default = "READ_WRITE"
}

variable "kube_etcd_svca_scopes" {
  description = "Service Account Scopes list"
  default = ["https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring.write","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"]
}

variable "kube_etcd_svca_email" {
  description = "Service Account Email"
  default = ""
}

variable "kube_etcd_target_size" {
  description = "Number of etcd nodes"
  default = "3"
}

################# Kube minions details ###########

variable "kube_minion_machine_type" {
  description = "Minion Machine Type, if not provided by default n1-standard-1 will be considered"
  default = "n1-standard-1"
}

variable "kube_minion_source_image" {
  description = "OS image name"
  default = "centos-6-v20190729"
}

variable "kube_minion_disk_size_gb" {
  description = "Disk size, by default 100GB"
  default ="100"
}

variable "kube_minion_disk_type" {
  description = "Disk type, pd-standard or pd-ssd"
  default = "pd-standard"
}

variable "kube_minion_network_interface" {
  description = "Network interface details"
  default = ""
}

variable "kube_minion_subnetwork" {
  description = "Subnetwork details"
  default = ""
}

variable "kube_minion_mode" {
  description = "Instance Mode"
  default = "READ_WRITE"
}

variable "kube_minion_svca_scopes" {
  description = "Service Account Scopes List"
  default = ["https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring.write","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"]
}

variable "kube_minion_svca_email" {
  description = "Service Account Email"
  default = ""
}
variable "kube_minion_target_size" {
  description = "Number of worker nodes/minions"
  default = "2"
}

##################### Ansible Machine Details ######### 
variable "kube_ansible_machine_type" {
  description = "Ansible Machine Type, if not provided by default n1-standard-1 will be considered"
  default = "n1-standard-1"
}

variable "kube_ansible_source_image" {
  description = "OS image name"
  default = "centos-6-v20190729"
}

variable "kube_ansible_disk_size_gb" {
  description = "Disk size, by default 100GB"
  default = "100"
}

variable "kube_ansible_disk_type" {
  description = "Disk type, pd-standard or pd-ssd"
  default = "pd-standard"
}

variable "kube_ansible_network_interface" {
  description = "Network interface details"
  default = ""
}

variable "kube_ansible_subnetwork" {
  description = "Subnetwork details"
  default = ""
}

variable "kube_ansible_mode" {
  description = "Instance Mode"
  default = "READ_WRITE"
}

variable "kube_ansible_svca_scopes" {
  description = "Service Account Scopes List"
  default = ["https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring.write","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"]
}

variable "kube_ansible_svca_email" {
  description = "Service Account Email"
  default = ""
}

variable "kube_ansible_target_size" {
  description = "Number of kubespray-ansible instaces"
  default = "1"
}
