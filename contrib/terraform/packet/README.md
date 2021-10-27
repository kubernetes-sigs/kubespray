# Kubernetes on Equinix Metal with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
[Equinix Metal](https://metal.equinix.com) ([formerly Packet](https://blog.equinix.com/blog/2020/10/06/equinix-metal-metal-and-more/)).

## Status

This will install a Kubernetes cluster on Equinix Metal. It should work in all locations and on most server types.

## Approach

The terraform configuration inspects variables found in
[variables.tf](variables.tf) to create resources in your Equinix Metal project.
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
- Account with Equinix Metal
- An SSH key pair

## SSH Key Setup

An SSH keypair is required so Ansible can access the newly provisioned nodes (Equinix Metal hosts). By default, the public SSH key defined in cluster.tfvars will be installed in authorized_key on the newly provisioned nodes (~/.ssh/id_rsa.pub). Terraform will upload this public key and then it will be distributed out to all the nodes. If you have already set this public key in Equinix Metal (i.e. via the portal), then set the public keyfile name in cluster.tfvars to blank to prevent the duplicate key from being uploaded which will cause an error.

If you don't already have a keypair generated (~/.ssh/id_rsa and ~/.ssh/id_rsa.pub), then a new keypair can be generated with the command:

```ShellSession
ssh-keygen -f ~/.ssh/id_rsa
```

## Terraform

Terraform will be used to provision all of the Equinix Metal resources with base software as appropriate.

### Configuration

#### Inventory files

Create an inventory directory for your cluster by copying the existing sample and linking the `hosts` script (used to build the inventory based on Terraform state):

```ShellSession
cp -LRp contrib/terraform/packet/sample-inventory inventory/$CLUSTER
cd inventory/$CLUSTER
ln -s ../../contrib/terraform/packet/hosts
```

This will be the base for subsequent Terraform commands.

#### Equinix Metal API access

Your Equinix Metal API key must be available in the `PACKET_AUTH_TOKEN` environment variable.
This key is typically stored outside of the code repo since it is considered secret.
If someone gets this key, they can startup/shutdown hosts in your project!

For more information on how to generate an API key or find your project ID, please see
[Accounts Index](https://metal.equinix.com/developers/docs/accounts/).

The Equinix Metal Project ID associated with the key will be set later in `cluster.tfvars`.

For more information about the API, please see [Equinix Metal API](https://metal.equinix.com/developers/api/).

Example:

```ShellSession
export PACKET_AUTH_TOKEN="Example-API-Token"
```

Note that to deploy several clusters within the same project you need to use [terraform workspace](https://www.terraform.io/docs/state/workspaces.html#using-workspaces).

#### Cluster variables

The construction of the cluster is driven by values found in
[variables.tf](variables.tf).

For your cluster, edit `inventory/$CLUSTER/cluster.tfvars`.

The `cluster_name` is used to set a tag on each server deployed as part of this cluster.
This helps when identifying which hosts are associated with each cluster.

While the defaults in variables.tf will successfully deploy a cluster, it is recommended to set the following values:

- cluster_name = the name of the inventory directory created above as $CLUSTER
- packet_project_id = the Equinix Metal Project ID associated with the Equinix Metal API token above

#### Enable localhost access

Kubespray will pull down a Kubernetes configuration file to access this cluster by enabling the
`kubeconfig_localhost: true` in the Kubespray configuration.

Edit `inventory/$CLUSTER/group_vars/k8s_cluster/k8s_cluster.yml` and comment back in the following line and change from `false` to `true`:
`\# kubeconfig_localhost: false`
becomes:
`kubeconfig_localhost: true`

Once the Kubespray playbooks are run, a Kubernetes configuration file will be written to the local host at `inventory/$CLUSTER/artifacts/admin.conf`

#### Terraform state files

In the cluster's inventory folder, the following files might be created (either by Terraform
or manually), to prevent you from pushing them accidentally they are in a
`.gitignore` file in the `terraform/packet` directory :

- `.terraform`
- `.tfvars`
- `.tfstate`
- `.tfstate.backup`

You can still add them manually if you want to.

### Initialization

Before Terraform can operate on your cluster you need to install the required
plugins. This is accomplished as follows:

```ShellSession
cd inventory/$CLUSTER
terraform init ../../contrib/terraform/packet
```

This should finish fairly quickly telling you Terraform has successfully initialized and loaded necessary modules.

### Provisioning cluster

You can apply the Terraform configuration to your cluster with the following command
issued from your cluster's inventory directory (`inventory/$CLUSTER`):

```ShellSession
terraform apply -var-file=cluster.tfvars ../../contrib/terraform/packet
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook -i hosts ../../cluster.yml
```

### Destroying cluster

You can destroy your new cluster with the following command issued from the cluster's inventory directory:

```ShellSession
terraform destroy -var-file=cluster.tfvars ../../contrib/terraform/packet
```

If you've started the Ansible run, it may also be a good idea to do some manual cleanup:

- Remove SSH keys from the destroyed cluster from your `~/.ssh/known_hosts` file
- Clean up any temporary cache files: `rm /tmp/$CLUSTER-*`

### Debugging

You can enable debugging output from Terraform by setting `TF_LOG` to `DEBUG` before running the Terraform command.

## Ansible

### Node access

#### SSH

Ensure your local ssh-agent is running and your ssh key has been added. This
step is required by the terraform provisioner:

```ShellSession
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa
```

If you have deployed and destroyed a previous iteration of your cluster, you will need to clear out any stale keys from your SSH "known hosts" file ( `~/.ssh/known_hosts`).

#### Test access

Make sure you can connect to the hosts.  Note that Flatcar Container Linux by Kinvolk will have a state `FAILED` due to Python not being present.  This is okay, because Python will be installed during bootstrapping, so long as the hosts are not `UNREACHABLE`.

```ShellSession
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

```ShellSession
ansible-playbook --become -i inventory/$CLUSTER/hosts cluster.yml
```

This will take some time as there are many tasks to run.

## Kubernetes

### Set up kubectl

- [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) on the localhost.
- Verify that Kubectl runs correctly

```ShellSession
kubectl version
```

- Verify that the Kubernetes configuration file has been copied over

```ShellSession
cat inventory/alpha/$CLUSTER/admin.conf
```

- Verify that all the nodes are running correctly.

```ShellSession
kubectl version
kubectl --kubeconfig=inventory/$CLUSTER/artifacts/admin.conf  get nodes
```

## What's next

Try out your new Kubernetes cluster with the [Hello Kubernetes service](https://kubernetes.io/docs/tasks/access-application-cluster/service-access-application-cluster/).
