## @author : Vinayaka V Ladwa
## @maintainer : Vinayaka V Ladwa
## @email : vinayakladwa@gmail.com
## @version : v1

################## GCP Provider ###############################################
provider "google" {
  credentials = file("./gcp-auth-config-json/account.json")
  region      = var.region
  project = var.gcp_project_id
  version = "~> 3.16"
}

################### Deleting the terraform existing inventory file #######################
resource "null_resource" "delete_inv_file" {
  provisioner "local-exec" {
    command = "rm -f ${var.env}-inventory.ini"
  }
}


/* 
module=k8s_master_comp is used to create the kubernetes master node template
and instances group based on the count provided in the cluster.tfvars or variables.tf files.
*/

module "k8s_master_comp" {
  env_name          = "${var.env}"
  gcp_project_id = "${var.gcp_project_id}"
  component         = "master"
  source            = "../modules/template"
  template_name     = "${var.env}-master"
  machine_type      = "${var.kube_master_machine_type}"
  source_image      = "${var.kube_master_source_image}"
  disk_size_gb      = "${var.kube_master_disk_size_gb}"
  disk_type         = "${var.kube_master_disk_type}"
  network_interface = "${var.kube_master_network_interface}"
  subnetwork        = "${var.kube_master_subnetwork}"
  mode              = "${var.kube_master_mode}"
  svca_email        = "${var.kube_master_svca_email}"
  svca_scopes       = "${var.kube_master_svca_scopes}"
  target_size       = "${var.kube_master_target_size}"
  region            = "${var.region}"
}

data "google_compute_instance" "master_ssh_details" {
  self_link = "${module.k8s_master_comp.ans_ssh_name}"
}

output "master_ssh_ip" {
  value = "${data.google_compute_instance.master_ssh_details.network_interface.*.network_ip}"
}

/* 
module=k8s_etcd_comp is used to create the kubernetes etcd node template
and instances group based on the count provided in the cluster.tfvars or variables.tf files.
*/

module "k8s_etcd_comp" {
  env_name          = "${var.env}"
  gcp_project_id = "${var.gcp_project_id}"
  component         = "etcd"
  source            = "../modules/template"
  template_name     = "${var.env}-etcd"
  machine_type      = "${var.kube_etcd_machine_type}"
  source_image      = "${var.kube_etcd_source_image}"
  disk_size_gb      = "${var.kube_etcd_disk_size_gb}"
  disk_type         = "${var.kube_etcd_disk_type}"
  network_interface = "${var.kube_etcd_network_interface}"
  subnetwork        = "${var.kube_etcd_subnetwork}"
  mode              = "${var.kube_etcd_mode}"
  svca_email        = "${var.kube_etcd_svca_email}"
  svca_scopes       = "${var.kube_etcd_svca_scopes}"
  target_size       = "${var.kube_etcd_target_size}"
  region            = "${var.region}"
}



/* 
module=k8s_default_comp is used to create the kubernetes worker nodes/minions template 
and instances group based on the count provided in the cluster.tfvars or variables.tf files.
*/

module "k8s_default_comp" {
  env_name          = "${var.env}"
  gcp_project_id = "${var.gcp_project_id}"
  component         = "minion"
  source            = "../modules/template"
  template_name     = "${var.env}-minion"
  machine_type      = "${var.kube_minion_machine_type}"
  source_image      = "${var.kube_minion_source_image}"
  disk_size_gb      = "${var.kube_minion_disk_size_gb}"
  disk_type         = "${var.kube_minion_disk_type}"
  network_interface = "${var.kube_minion_network_interface}"
  subnetwork        = "${var.kube_minion_subnetwork}"
  mode              = "${var.kube_minion_mode}"
  svca_email        = "${var.kube_minion_svca_email}"
  svca_scopes       = "${var.kube_minion_svca_scopes}"
  target_size       = "${var.kube_minion_target_size}"
  region            = "${var.region}"
}



/* 
module=k8s_ansible_comp is used to create the kubespray-ansible node template
and instances group based on the count provided as configurations below.
This instance will be used to download the kubespray and execute the cluster.yml playbook.
*/
module "k8s_ansible_comp" {
  env_name          = "${var.env}"
  gcp_project_id = "${var.gcp_project_id}"
  component         = "ansible"
  source            = "../modules/template"
  template_name     = "${var.env}-kubespray"
  machine_type      = "${var.kube_ansible_machine_type}"
  source_image      = "${var.kube_ansible_source_image}"
  disk_size_gb      = "${var.kube_ansible_disk_size_gb}"
  disk_type         = "${var.kube_ansible_disk_type}"
  network_interface = "${var.kube_ansible_network_interface}"
  subnetwork        = "${var.kube_ansible_subnetwork}"
  mode              = "${var.kube_ansible_mode}"
  svca_email        = "${var.kube_ansible_svca_email}"
  svca_scopes       = "${var.kube_ansible_svca_scopes}"
  target_size       = "${var.kube_ansible_target_size}"
  region            = "${var.region}"
}

data "google_compute_instance" "ansible_ssh_machine_details" {
  self_link = "${module.k8s_ansible_comp.ans_ssh_name}"
}

output "ansible_ssh_ip" {
  value = "${data.google_compute_instance.ansible_ssh_machine_details.network_interface[0].network_ip}"
}

resource "null_resource" "ssh_ansible" {
  connection {
    host        = data.google_compute_instance.ansible_ssh_machine_details.network_interface[0].network_ip
    type        = "ssh"
    user        = var.user_name
    timeout     = "500s"
    private_key = file("../kube_configurations/ssh-key")
  }
  provisioner "remote-exec" {
    inline = [
      "sudo yum install python-pip -y",
      "sudo yum install git -y ",
      "sudo pip install netaddr",
      "sudo pip install logging",
      "mkdir -p ${var.kube_automation_folder}",
      "cd ${var.kube_automation_folder} && git clone ${var.kubespray_repo_url}",
      "cd ${var.kube_automation_folder}/kubespray && sudo pip install -r requirements.txt"
    ]
  }
  provisioner "file" {
    source      = "${var.env}-inventory.ini"
    destination = "${var.kube_automation_folder}/${var.env}-inventory.ini"
  }

  provisioner "file" {
    source      = "../kube_configurations/GenerateInventoryFile.py"
    destination = "${var.kube_automation_folder}/GenerateInventoryFile.py"
  }

  provisioner "file" {
    source      = "./gcp-auth-config-json/account.json"
    destination = "${var.kube_automation_folder}/account.json"
  }
  provisioner "file" {
    source      = "../kube_configurations/ssh-key"
    destination = "${var.kube_automation_folder}/key"
  }
  provisioner "remote-exec" {
    inline = [
      "cd ${var.kube_automation_folder} && chmod 400 key && chmod 777 GenerateInventoryFile.py && mv ${var.env}-inventory.ini inventory_hosts.ini",
      "cd ${var.kube_automation_folder} && python GenerateInventoryFile.py ${var.kube_automation_folder} ${var.user_name}",
      "cd ${var.kube_automation_folder}/kubespray && ansible-playbook -i inventory/cluster/inventory_hosts.ini -b -v cluster.yml 2>&1 | tee outfile",
    ]
  }
}
