# Kubernetes on Packet with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
[Packet](https://www.packet.com).

## Status

This will install a Kubernetes cluster on Packet bare metal. It should work in all locations and on most server types.

## Approach
The terraform configuration inspects variables found in
[variables.tf](variables.tf) to create resources in your Packet project.
There is a [python script](../terraform.py) that reads the generated`.tfstate`
file to generate a dynamic inventory that is consumed by [cluster.yml](../../..//cluster.yml)
to actually install Kubernetes with Kubespray.

### Kubernetes Nodes
You can create many different kubernetes topologies by setting the number of
different classes of hosts.
- Master nodes with etcd: `number_of_k8s_masters` variable
- Master nodes without etcd: `number_of_k8s_masters_no_etcd` variable
- Standalone etcd hosts: `number_of_etcd` variable
- Kubernetes worker nodes: `number_of_k8s_nodes` variable

Note that the Ansible script will report an invalid configuration if you wind up
with an *even number* of etcd instances since that is not a valid configuration. This
restriction includes standalone etcd nodes that are deployed in a cluster along with
master nodes with etcd replicas. As an example, if you have three master nodes with
etcd replicas and three standalone etcd nodes, the script will fail since there are
now six total etcd replicas.

## Requirements

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html)
- Install dependencies: `sudo pip install -r requirements.txt`
- Account with Packet Host
- you have an SSH key pair

## Terraform
Terraform will be used to provision all of the Packet resources with base software as appropriate.

### Configuration

#### Inventory files

Create an inventory directory for your cluster by copying the existing sample and linking the `hosts` script (used to build the inventory based on Terraform state):

```ShellSession
$ cp -LRp contrib/terraform/packet/sample-inventory inventory/$CLUSTER
$ cd inventory/$CLUSTER
$ ln -s ../../contrib/terraform/packet/hosts
```

This will be the base for subsequent Terraform commands.

#### Packet API access

Your Packet API key must be available in the `PACKET_AUTH_TOKEN` environment variable.
This key is typically stored outside of the code repo since it is considered secret.
If someone gets this key, they can startup/shutdown hosts in your project!

For more information on how to generate an API key or find your project ID, please see:
https://support.packet.com/kb/articles/api-integrations

The Packet Project ID associated with the key will be set later in cluster.tf.

For more information about the API, please see:
https://www.packet.com/developers/api/

Example:
```ShellSession
$ export PACKET_AUTH_TOKEN="Example-API-Token"
```

Note that to deploy several clusters within the same project you need to use [terraform workspace](https://www.terraform.io/docs/state/workspaces.html#using-workspaces).

#### Cluster variables
The construction of the cluster is driven by values found in
[variables.tf](variables.tf).

For your cluster, edit `inventory/$CLUSTER/cluster.tf`.

The `cluster_name` is used to set a tag on each server deployed as part of this cluster.
This helps when identifying which hosts are associated with each cluster.

While the defaults in variables.tf will successfully deploy a cluster, it is recommended to set the following values:

* cluster_name = the name of the inventory directory created above as $CLUSTER
* packet_project_id = the Packet Project ID associated with the Packet API token above

#### Terraform state files

In the cluster's inventory folder, the following files might be created (either by Terraform
or manually), to prevent you from pushing them accidentally they are in a
`.gitignore` file in the `terraform/packet` directory :

* `.terraform`
* `.tfvars`
* `.tfstate`
* `.tfstate.backup`

You can still add them manually if you want to.

### Initialization

Before Terraform can operate on your cluster you need to install the required
plugins. This is accomplished as follows:

```ShellSession
$ cd inventory/$CLUSTER
$ terraform init ../../contrib/terraform/packet
```

This should finish fairly quickly telling you Terraform has successfully initialized and loaded necessary modules.

### Provisioning cluster
You can apply the Terraform configuration to your cluster with the following command
issued from your cluster's inventory directory (`inventory/$CLUSTER`):
```ShellSession
$ terraform apply -var-file=cluster.tf ../../contrib/terraform/packet
$ export ANSIBLE_HOST_KEY_CHECKING=False
$ ansible-playbook -i hosts ../../cluster.yml
```

### Destroying cluster
You can destroy your new cluster with the following command issued from the cluster's inventory directory:

```ShellSession
$ terraform destroy -var-file=cluster.tf ../../contrib/terraform/packet
```

If you've started the Ansible run, it may also be a good idea to do some manual cleanup:

* remove SSH keys from the destroyed cluster from your `~/.ssh/known_hosts` file
* clean up any temporary cache files: `rm /tmp/$CLUSTER-*`

### Debugging
You can enable debugging output from Terraform by setting `TF_LOG` to `DEBUG` before running the Terraform command.

## Ansible

### Node access

#### SSH

Ensure your local ssh-agent is running and your ssh key has been added. This
step is required by the terraform provisioner:

```
$ eval $(ssh-agent -s)
$ ssh-add ~/.ssh/id_rsa
```

If you have deployed and destroyed a previous iteration of your cluster, you will need to clear out any stale keys from your SSH "known hosts" file ( `~/.ssh/known_hosts`).

#### Test access

Make sure you can connect to the hosts.  Note that Container Linux by CoreOS will have a state `FAILED` due to Python not being present.  This is okay, because Python will be installed during bootstrapping, so long as the hosts are not `UNREACHABLE`.

```
$ ansible -i inventory/$CLUSTER/hosts -m ping all
example-k8s_node-1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
example-etcd-1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
example-k8s-master-1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

If it fails try to connect manually via SSH.  It could be something as simple as a stale host key.

### Deploy Kubernetes

```
$ ansible-playbook --become -i inventory/$CLUSTER/hosts cluster.yml
```

This will take some time as there are many tasks to run.

## Kubernetes

### Set up kubectl
1. [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) on your workstation
2. List Kubernetes certificates & keys:
```
ssh root@[master-ip] sudo ls /etc/kubernetes/ssl/
```
3. Get `admin`'s certificates and keys:
```
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-kube-master-1-key.pem > admin-key.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-kube-master-1.pem > admin.pem
ssh root@[master-ip] sudo cat /etc/kubernetes/ssl/ca.pem > ca.pem
```
5. Configure kubectl:
```ShellSession
$ kubectl config set-cluster default-cluster --server=https://[master-ip]:6443 \
    --certificate-authority=ca.pem

$ kubectl config set-credentials default-admin \
    --certificate-authority=ca.pem \
    --client-key=admin-key.pem \
    --client-certificate=admin.pem

$ kubectl config set-context default-system --cluster=default-cluster --user=default-admin
$ kubectl config use-context default-system
```
7. Check it:
```
kubectl version
```

## What's next

Try out your new Kubernetes cluster with the [Hello Kubernetes service](https://kubernetes.io/docs/tasks/access-application-cluster/service-access-application-cluster/).
