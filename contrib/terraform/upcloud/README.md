# Kubernetes on UpCloud with Terraform

Provision a Kubernetes cluster on [UpCloud](https://upcloud.com/) using Terraform and Kubespray

## Overview

The setup looks like following

```text
   Kubernetes cluster
+-----------------------+
|   +--------------+    |
|   | +--------------+  |
|   | |              |  |
|   | | Master/etcd  |  |
|   | | node(s)      |  |
|   +-+              |  |
|     +--------------+  |
|           ^           |
|           |           |
|           v           |
|   +--------------+    |
|   | +--------------+  |
|   | |              |  |
|   | |    Worker    |  |
|   | |    node(s)   |  |
|   +-+              |  |
|     +--------------+  |
+-----------------------+
```

## Requirements

* Terraform 0.13.0 or newer

## Quickstart

NOTE: Assumes you are at the root of the kubespray repo.

For authentication in your  cluster you can use the environment variables.

```bash
export TF_VAR_UPCLOUD_USERNAME=username
export TF_VAR_UPCLOUD_PASSWORD=password
```

To allow API access to your UpCloud account, you need to allow API connections by visiting [Account-page](https://hub.upcloud.com/account) in your UpCloud Hub.

Copy the cluster configuration file.

```bash
CLUSTER=my-upcloud-cluster
cp -r inventory/sample inventory/$CLUSTER
cp contrib/terraform/upcloud/cluster-settings.tfvars inventory/$CLUSTER/
export ANSIBLE_CONFIG=ansible.cfg
cd inventory/$CLUSTER
```

Edit  `cluster-settings.tfvars`  to match your requirement.

Run Terraform to create the infrastructure.

```bash
terraform init ../../contrib/terraform/upcloud
terraform apply --var-file cluster-settings.tfvars \
    -state=tfstate-$CLUSTER.tfstate \
     ../../contrib/terraform/upcloud/
```

You should now have a inventory file named `inventory.ini` that you can use with kubespray.
You can use the inventory file with kubespray to set up a cluster.

It is a good idea to check that you have basic SSH connectivity to the nodes. You can do that by:

```bash
ansible -i inventory.ini -m ping all
```

You can setup Kubernetes with kubespray using the generated inventory:

```bash
ansible-playbook -i inventory.ini ../../cluster.yml -b -v
```

## Teardown

You can teardown your infrastructure using the following Terraform command:

```bash
terraform destroy --var-file cluster-settings.tfvars \
      -state=tfstate-$CLUSTER.tfstate \
      ../../contrib/terraform/upcloud/
```

## Variables

* `hostname`: A valid domain name, e.g. example.com. The maximum length is 128 characters.
* `template_name`: The name or UUID  of a base image
* `username`: a user to access the nodes
* `ssh_public_keys`: List of public SSH keys to install on all machines
* `zone`: The zone where to run the cluster
* `machines`: Machines to provision. Key of this object will be used as the name of the machine
  * `node_type`: The role of this node *(master|worker)*
  * `cpu`: number of cpu cores
  * `mem`: memory size in MB
  * `disk_size`: The size of the storage in GB
