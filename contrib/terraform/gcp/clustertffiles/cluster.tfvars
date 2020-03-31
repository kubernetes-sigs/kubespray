###### Environment Details or ######
env = "open-source" 

######### user_name #
user_name = "app"

######## Region ##############
region = "us-central1"

######### Kube automation folder where you would like to clone the kubespray project #################
kube_automation_folder ="/home/app/kube_automation"

########### Kubespray repo URL hosted  in the github ####
kubespray_repo_url = "https://USER_NAME:PASSWORD@github.com/kubernetes-sigs/kubespray.git"

######### GCP project name ############### 
gcp_project_id = ""

############ Kube Master Node Details ####################
kube_master_machine_type = "n1-standard-8"
kube_master_source_image = "centos7" # pd-standard or pd-ssd
kube_master_disk_size_gb = "100"
kube_master_disk_type = "pd-standard"
kube_master_network_interface = ""
kube_master_subnetwork = ""
kube_master_mode = "READ_WRITE"
kube_master_svca_email = ""
kube_master_svca_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
kube_master_target_size = "2"

####################### Kube Etcd Node Details #############
kube_etcd_machine_type = "n1-standard-8"
kube_etcd_source_image = "centos7"
kube_etcd_disk_size_gb = "100"
kube_etcd_disk_type = "pd-standard" # pd-standard or pd-ssd
kube_etcd_network_interface = ""
kube_etcd_subnetwork = ""
kube_etcd_mode = "READ_WRITE"
kube_etcd_svca_email = ""
kube_etcd_svca_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
kube_etcd_target_size = "3"


##################### Kube Minion Node Details #################
kube_minion_machine_type = "n1-standard-8"
kube_minion_source_image = "centos7"
kube_minion_disk_size_gb = "500"
kube_minion_disk_type = "pd-standard" # pd-standard or pd-ssd
kube_minion_network_interface = ""
kube_minion_subnetwork = ""
kube_minion_mode = "READ_WRITE"
kube_minion_svca_email = ""
kube_minion_svca_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
kube_minion_target_size = "2"

############## Ansible Instance Details ################
kube_ansible_machine_type = "n1-standard-8"
kube_ansible_source_image = "centos7"
kube_ansible_disk_size_gb = "50"
kube_ansible_disk_type = "pd-standard" # pd-standard or pd-ssd
kube_ansible_network_interface = ""
kube_ansible_subnetwork = ""
kube_ansible_mode = "READ_WRITE"
kube_ansible_svca_email = ""
kube_ansible_svca_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
kube_ansible_target_size = "1"
