# Packet

Kubespray provides support for bare metal deployments using the [Packet bare metal cloud](http://www.packet.com).
Deploying upon bare metal allows Kubernetes to run at locations where an existing public or private cloud might not exist such
as cell tower, edge collocated installations. The deployment mechanism used by Kubespray for Packet is similar to that used for
AWS and OpenStack clouds (notably using Terraform to deploy the infrastructure). Terraform uses the Packet provider plugin
to provision and configure hosts which are then used by the Kubespray Ansible playbooks. The Ansible inventory is generated
dynamically from the Terraform state file.

## Local Host Configuration

To perform this installation, you will need a localhost to run Terraform/Ansible (laptop, VM, etc) and an account with Packet.
In this example, we're using an m1.large CentOS 7 OpenStack VM as the localhost to kickoff the Kubernetes installation.
You'll need Ansible, Git, and PIP.

```bash
sudo yum install epel-release
sudo yum install ansible
sudo yum install git
sudo yum install python-pip
```

## Playbook SSH Key

An SSH key is needed by Kubespray/Ansible to run the playbooks.
This key is installed into the bare metal hosts during the Terraform deployment.
You can generate a key new key or use an existing one.

```bash
ssh-keygen -f ~/.ssh/id_rsa
```

## Install Terraform

Terraform is required to deploy the bare metal infrastructure. The steps below are for installing on CentOS 7.
[More terraform installation options are available.](https://learn.hashicorp.com/terraform/getting-started/install.html)

Grab the latest version of Terraform and install it.

```bash
echo "https://releases.hashicorp.com/terraform/$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')/terraform_$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')_linux_amd64.zip"
sudo yum install unzip
sudo unzip terraform_0.12.24_linux_amd64.zip -d /usr/local/bin/
```

## Download Kubespray

Pull over Kubespray and setup any required libraries.

```bash
git clone https://github.com/kubernetes-sigs/kubespray
cd kubespray
sudo pip install -r requirements.txt
```

## Cluster Definition

In this example, a new cluster called "alpha" will be created.

```bash
cp -LRp contrib/terraform/packet/sample-inventory inventory/alpha
cd inventory/alpha/
ln -s ../../contrib/terraform/packet/hosts
```

Details about the cluster, such as the name, as well as the authentication tokens and project ID
for Packet need to be defined. To find these values see [Packet API Integration](https://support.packet.com/kb/articles/api-integrations)

```bash
vi cluster.tfvars
```

* cluster_name = alpha
* packet_project_id = ABCDEFGHIJKLMNOPQRSTUVWXYZ123456
* public_key_path = 12345678-90AB-CDEF-GHIJ-KLMNOPQRSTUV

## Deploy Bare Metal Hosts

Initializing Terraform will pull down any necessary plugins/providers.

```bash
terraform init ../../contrib/terraform/packet/
```

Run Terraform to deploy the hardware.

```bash
terraform apply -var-file=cluster.tfvars ../../contrib/terraform/packet
```

## Run Kubespray Playbooks

With the bare metal infrastructure deployed, Kubespray can now install Kubernetes and setup the cluster.

```bash
ansible-playbook --become -i inventory/alpha/hosts cluster.yml
```
