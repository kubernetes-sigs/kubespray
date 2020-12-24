provider "google" {
  credentials = file(var.keyfile_location)
  region      = var.region
  project     = var.gcp_project_id
  version     = "~> 3.48"
}

module "kubernetes" {
  source = "./modules/kubernetes-cluster"
  region = var.region
  prefix = var.prefix

  machines    = var.machines
  ssh_pub_key = var.ssh_pub_key

  master_sa_email  = var.master_sa_email
  master_sa_scopes = var.master_sa_scopes
  worker_sa_email  = var.worker_sa_email
  worker_sa_scopes = var.worker_sa_scopes

  ssh_whitelist        = var.ssh_whitelist
  api_server_whitelist = var.api_server_whitelist
  nodeport_whitelist   = var.nodeport_whitelist
}
