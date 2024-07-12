# Kubernetes on NIFCLOUD with Terraform

Provision a Kubernetes cluster on [NIFCLOUD](https://pfs.nifcloud.com/) using Terraform and Kubespray

## Overview

The setup looks like following

```text
                              Kubernetes cluster
                        +----------------------------+
+---------------+       |   +--------------------+   |
|               |       |   | +--------------------+ |
| API server LB +---------> | |                    | |
|               |       |   | | Control Plane/etcd | |
+---------------+       |   | | node(s)            | |
                        |   +-+                    | |
                        |     +--------------------+ |
                        |           ^                |
                        |           |                |
                        |           v                |
                        |   +--------------------+   |
                        |   | +--------------------+ |
                        |   | |                    | |
                        |   | |        Worker      | |
                        |   | |        node(s)     | |
                        |   +-+                    | |
                        |     +--------------------+ |
                        +----------------------------+
```

## Requirements

* Terraform 1.3.7

## Quickstart

### Export Variables

* Your NIFCLOUD credentials:

  ```bash
  export NIFCLOUD_ACCESS_KEY_ID=<YOUR ACCESS KEY>
  export NIFCLOUD_SECRET_ACCESS_KEY=<YOUR SECRET ACCESS KEY>
  ```

* The SSH KEY used to connect to the instance:
  * FYI: [Cloud Help(SSH Key)](https://pfs.nifcloud.com/help/ssh.htm)

  ```bash
  export TF_VAR_SSHKEY_NAME=<YOUR SSHKEY NAME>
  ```

* The IP address to connect to bastion server:

  ```bash
  export TF_VAR_working_instance_ip=$(curl ifconfig.me)
  ```

### Create The Infrastructure

* Run terraform:

  ```bash
  terraform init
  terraform apply -var-file ./sample-inventory/cluster.tfvars
  ```

### Setup The Kubernetes

* Generate cluster configuration file:

  ```bash
  ./generate-inventory.sh > sample-inventory/inventory.ini
  ```

* Export Variables:

  ```bash
  BASTION_IP=$(terraform output -json | jq -r '.kubernetes_cluster.value.bastion_info | to_entries[].value.public_ip')
  API_LB_IP=$(terraform output -json | jq -r '.kubernetes_cluster.value.control_plane_lb')
  CP01_IP=$(terraform output -json | jq -r '.kubernetes_cluster.value.control_plane_info | to_entries[0].value.private_ip')
  export ANSIBLE_SSH_ARGS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ProxyCommand=\"ssh root@${BASTION_IP} -W %h:%p\""
  ```

* Set ssh-agent"

  ```bash
  eval `ssh-agent`
  ssh-add <THE PATH TO YOUR SSH KEY>
  ```

* Run cluster.yml playbook:

  ```bash
  cd ./../../../
  ansible-playbook -i contrib/terraform/nifcloud/inventory/inventory.ini cluster.yml
  ```

### Connecting to Kubernetes

* [Install kubectl](https://kubernetes.io/docs/tasks/tools/) on the localhost
* Fetching kubeconfig file:

  ```bash
  mkdir -p ~/.kube
  scp -o ProxyCommand="ssh root@${BASTION_IP} -W %h:%p" root@${CP01_IP}:/etc/kubernetes/admin.conf ~/.kube/config
  ```

* Rewrite /etc/hosts

  ```bash
  sudo echo "${API_LB_IP} lb-apiserver.kubernetes.local" >> /etc/hosts
  ```

* Run kubectl

  ```bash
  kubectl get node
  ```

## Variables

* `region`: Region where to run the cluster
* `az`: Availability zone where to run the cluster
* `private_ip_bn`: Private ip address of bastion server
* `private_network_cidr`:  Subnet of private network
* `instances_cp`: Machine to provision as Control Plane. Key of this object will be used as part of the machine' name
  * `private_ip`: private ip address of machine
* `instances_wk`: Machine to provision as Worker Node. Key of this object will be used as part of the machine' name
  * `private_ip`: private ip address of machine
* `instance_key_name`: The key name of the Key Pair to use for the instance
* `instance_type_bn`: The instance type of bastion server
* `instance_type_wk`: The instance type of worker node
* `instance_type_cp`: The instance type of control plane
* `image_name`: OS image used for the instance
* `working_instance_ip`: The IP address to connect to bastion server
* `accounting_type`: Accounting type. (1: monthly, 2: pay per use)
