## Kubernetes on GCP with Terraform

Provision a Kubernetes cluster on GCP using [Terraform](https://www.terraform.io) and [Kubespray](https://github.com/kubernetes-sigs/kubespray.git)

![Workflow](Workflow.svg)

**Overview:**

This project will create:

* Creation of **Kubernetes master** Instance template and Instance Group (1 & 2).The Compute instances are created in different zones.
* Creation of **Kubernetes etcd** Instance template and Instance Group (3 & 4).The Compute instances are created in different zones.
* Creation of **Kubernetes worker nodes/minions** Instance template and Instance Group (5 & 6).The Compute instances are created in different zones.
* Creation of **kubespray ansible** Instance Template and Instane Group(7 & 8).
* Installing the pre-requisite packages/modules/Scripts (pip,git,etc) required for kubespray(9).
* Download the kubespray or git clone the kubespray project(9). 
* Coping the required scripts to generate hosts inventory file. Which will be provided as input to the kubespray cluster.yml playbook to setup kubernetes cluster(9). 
* Login to the kubespray ansible instance and execute the **cluster.yml** ansible-playbook to setup cluster. The cluster execution details will be shown in terminal and also the output is redirected to the **“output”** file(10).
* Kubespray-Ansible Machine Ip and One of the Kube-master Ip will be displayed as part of output. 


## Status
This will install a Kubernetes cluster on GCP. 

## Approach
The terraform configuration inspects variables found in [variables.tf](./clustertffiles/variables.tf) to create resources in GCP.

The terraform script will take care of creating Master nodes,etcd nodes,worker nodes/minions, kubespray-ansible-node based on the configuration details. 

There is a [python script](./kube_configurations/GenerateInventoryFile.py) that generates a dynamic inventory that is consumed by the kubespray cluster.yml.

### Kubernetes Nodes
You can create different kubernetes topologies by setting the below mentioned variable to indicate number of hosts.

- Master nodes: `kube_master_target_size` variable
- Etcd nodes : `kube_etcd_target_size` variable
- Kubernetes worker nodes or minions: `kube_minion_target_size` variable

- Kubespray ansible node: `kube_ansible_target_size` variable

Note that the kubespray Ansible script will report an invalid configuration if you wind up
with an *even number* of etcd instances since that is not a valid configuration. Also it is recommended to have multiple master nodes for high availability.

## Prerequisites

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html)
- [Service account key json](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) (Appropirate roles to be assinged to service account to create computes)
- Centos or Redhat os to be used for kubespray ansible instance.
- You have a pair of keys generated which is the part of image that can be used to secure the new hosts.
- [Kubespray](https://github.com/kubernetes-sigs/kubespray.git). Make sure the project name is kubespray.


### Configuration

#### Service Account key json file
Details from service account key json file should be updated in the [account.json](./clustertffiles/gcp-auth-config-json/account.json) file
The Project ID associated with the service account key should be set in the [variables.tf](./clustertffiles/variables.tf)

Note: To deploy several clusters within the same project you need to use [terraform workspace](https://www.terraform.io/docs/state/workspaces.html#using-workspaces).

#### SSH Key Setup
SSH keypair is required by Kubespray-Ansible to access the newly provisioned Instances on GCP.When ssh keys are generated for the user 

* private key to be placed in the file [key](./kube_configurations/ssh-key).
* Public key to be added at the project wide level. [Refer link to add-ssh-key at project level](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys) 

#### Cluster variables:

The creation of the cluster is driven by values found in [variables.tf](./clustertffiles/variables.tf) or (cluster.tfvars)[./clustertffiles/cluster.tfvars]

For your cluster, edit `clustertffiles/cluster.tfvars`.

`env` variable is used to set a tag on each server deployed as part of this cluster.This helps with indentification of hosts associated with each cluster.

`region` variable is used to set in which region "Compute Instance templates and Compute Instance Groups" needs to be created.

`gcp_project` variable is used to set the GCP project_id.

`user_name` variable is used to set user name in kubespray inventory host file.

Ensure that username set for `user_name` matches the username used for SSH key generation.

`kube_automation_folder` the folder location where kubespray should be downloaded. The default value of this is '/home/app/kubespray', where `app` is the newly created user as part of SSH key setup.

`kubespray_repo_url` the kubespray git project url, user name and password to be passed in the URL. If required user credentials to be passed in the url like https://username:password@github.com/username/kubespray.git

`kube_{component}_machine_type` variable is used to set Compute Instance machine type.

`kube_{component}_source_image` variable is used to set OS Image type. This determines the operating system installed on the system.

`kube_{component}_disk_size_gb` variable is used to set Compute Instance disk size. Specifies the size of the disk in base-2 GB.

`kube_{component}_disk_type` variable is used to set Compute Instance disk type.

`kube_{component}_network_interface` variable is used set Network Interface.

`kube_{component}_subnetwork`variable is used to set subnetwork.

`kube_{component}_mode` is used to set mode in which to attach this disk, either READ_WRITE or READ_ONLY.

`kube_{component}_svca_email` variable is used to set email address of the service account.

`kube_{component}_svca_scopes` variable is used to set list of scopes to be made available to the service account.

`kube_{component}_target_size` variable is used to set total number of instances in the group.

**Where component can be either : master,etcd,minion or ansible**

[variables.tf](./clustertffiles/variables.tf) or (cluster.tfvars)[./clustertffiles/cluster.tfvars] files are updated with default values.

### Initialization

Before Terraform can operate on your cluster you need to install the required plugins. 
This is accomplished as follows:

```ShellSession
$ cd clustertffiles
$ terraform init 
```


### Provisioning cluster
You can apply the Terraform configuration to your cluster with the following command issued from your cluster's clustertffiles directory (`cd clustertffiles`):
```ShellSession
$ terraform apply -var-file=cluster.tfvars
```

### Destroying cluster
You can destroy your new cluster with the following command issued from the cluster's clustertffiles directory:

```ShellSession
$ terraform destroy -var-file=cluster.tfvars
```

On executing above command all the Instance templates, Instance Groups and Instances related to that cluster will be deleted. 

Please Note this action is irreversible. 

### Debugging
Enable debugging logs from Terraform by setting `TF_LOG` to `DEBUG` before "Provisioning cluster" step.

## Kubernetes 

### Master Node access

Login to the kube master node with Ip displayed as part of output. 

* Execute below command in kube master node to verify the version details:
```
kubectl version
```

* Verify that Kubernetes configuration file contains cluster details:
```
cat /root/.kube/config
```

* Verify that all the nodes are up & running, using below command:
```
kubectl get nodes
```
## What's next 

Try out your new Kubernetes cluster with the [Hello Kubernetes service](https://kubernetes.io/docs/tasks/access-application-cluster/service-access-application-cluster/).
