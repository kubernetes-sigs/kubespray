terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  credentials = file(var.keyfile_location)
  region      = var.region
  project     = var.gcp_project_id
}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"
  region = var.region
  prefix = var.prefix

  machines    = var.machines
  ssh_pub_key = var.ssh_pub_key

  master_sa_email    = var.master_sa_email
  master_sa_scopes   = var.master_sa_scopes
  master_preemptible = var.master_preemptible
  master_additional_disk_type = var.master_additional_disk_type
  worker_sa_email    = var.worker_sa_email
  worker_sa_scopes   = var.worker_sa_scopes
  worker_preemptible = var.worker_preemptible
  worker_additional_disk_type = var.worker_additional_disk_type

  ssh_whitelist        = var.ssh_whitelist
  api_server_whitelist = var.api_server_whitelist
  nodeport_whitelist   = var.nodeport_whitelist
  ingress_whitelist    = var.ingress_whitelist

  extra_ingress_firewalls = var.extra_ingress_firewalls
}
