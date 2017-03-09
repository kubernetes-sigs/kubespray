# Kubernetes on Openstack with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
Openstack.

## Status

This will install a Kubernetes cluster on an Openstack Cloud. It has been tested on a
OpenStack Cloud provided by [BlueBox](https://www.blueboxcloud.com/) and on OpenStack at [EMBL-EBI's](http://www.ebi.ac.uk/) [EMBASSY Cloud](http://www.embassycloud.org/). This should work on most modern installs of OpenStack that support the basic
services.

There are some assumptions made to try and ensure it will work on your openstack cluster.

* floating-ips are used for access, but you can have masters and nodes that don't use floating-ips if needed. You need currently at least 1 floating ip, which we would suggest is used on a master.
* you already have a suitable OS image in glance
* you already have both an internal network and a floating-ip pool created
* you have security-groups enabled


## Requirements

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html)

## Terraform

Terraform will be used to provision all of the OpenStack resources. It is also used to deploy and provision the software
requirements.

### Prep

#### OpenStack

Ensure your OpenStack **Identity v2** credentials are loaded in environment variables. This can be done by downloading a credentials .rc file from your OpenStack dashboard and sourcing it:

```
$ source ~/.stackrc
```

You will need two networks before installing, an internal network and
an external (floating IP Pool) network. The internet network can be shared as
we use security groups to provide network segregation. Due to the many
differences between OpenStack installs the Terraform does not attempt to create
these for you.

By default Terraform will expect that your networks are called `internal` and
`external`. You can change this by altering the Terraform variables `network_name` and `floatingip_pool`. This can be done on a new variables file or through environment variables.

A full list of variables you can change can be found at [variables.tf](variables.tf).

All OpenStack resources will use the Terraform variable `cluster_name` (
default `example`) in their name to make it easier to track. For example the
first compute resource will be named `example-kubernetes-1`.

#### Terraform

Ensure your local ssh-agent is running and your ssh key has been added. This
step is required by the terraform provisioner:

```
$ eval $(ssh-agent -s)
$ ssh-add ~/.ssh/id_rsa
```


Ensure that you have your Openstack credentials loaded into Terraform
environment variables. Likely via a command similar to:

```
$ echo Setting up Terraform creds && \
  export TF_VAR_username=${OS_USERNAME} && \
  export TF_VAR_password=${OS_PASSWORD} && \
  export TF_VAR_tenant=${OS_TENANT_NAME} && \
  export TF_VAR_auth_url=${OS_AUTH_URL}
```

If you want to provision master or node VMs that don't use floating ips, write on a `my-terraform-vars.tfvars` file, for example:

```
number_of_k8s_masters = "1"
number_of_k8s_masters_no_floating_ip = "2"
number_of_k8s_nodes_no_floating_ip = "1"
number_of_k8s_nodes = "0"
```
This will provision one VM as master using a floating ip, two additional masters using no floating ips (these will only have private ips inside your tenancy) and one VM as node, again without a floating ip.

Additionally, now the terraform based installation supports provisioning of a GlusterFS shared file system based on a separate set of VMs, running either a Debian or RedHat based set of VMs. To enable this, you need to add to your `my-terraform-vars.tfvars` the following variables:

```
# Flavour depends on your openstack installation, you can get available flavours through `nova flavor-list`
flavor_gfs_node = "af659280-5b8a-42b5-8865-a703775911da"
# This is the name of an image already available in your openstack installation.
image_gfs = "Ubuntu 15.10"
number_of_gfs_nodes_no_floating_ip = "3"
# This is the size of the non-ephemeral volumes to be attached to store the GlusterFS bricks.
gfs_volume_size_in_gb = "50"
# The user needed for the image choosen for GlusterFS.
ssh_user_gfs = "ubuntu"
```

If these variables are provided, this will give rise to a new ansible group called `gfs-cluster`, for which we have added ansible roles to execute in the ansible provisioning step. If you are using Container Linux by CoreOS, these GlusterFS VM necessarily need to be either Debian or RedHat based VMs, Container Linux by CoreOS cannot serve GlusterFS, but can connect to it through binaries available on hyperkube v1.4.3_coreos.0 or higher.


# Provision a Kubernetes Cluster on OpenStack

If not using a tfvars file for your setup, then execute:
```
terraform apply -state=contrib/terraform/openstack/terraform.tfstate contrib/terraform/openstack
openstack_compute_secgroup_v2.k8s_master: Creating...
  description: "" => "example - Kubernetes Master"
  name:        "" => "example-k8s-master"
  rule.#:      "" => "<computed>"
...
...
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

The state of your infrastructure has been saved to the path
below. This state is required to modify and destroy your
infrastructure, so keep it safe. To inspect the complete state
use the `terraform show` command.

State path: contrib/terraform/openstack/terraform.tfstate
```

Alternatively, if you wrote your terraform variables on a file `my-terraform-vars.tfvars`, your command would look like:
```
terraform apply -state=contrib/terraform/openstack/terraform.tfstate -var-file=my-terraform-vars.tfvars contrib/terraform/openstack
```

if you choose to add masters or nodes without floating ips (only internal ips on your OpenStack tenancy), this script will create as well a file `contrib/terraform/openstack/k8s-cluster.yml` with an ssh command for ansible to be able to access your machines tunneling  through the first floating ip used. If you want to manually handling the ssh tunneling to these machines, please delete or move that file. If you want to use this, just leave it there, as ansible will pick it up automatically.

Make sure you can connect to the hosts:

```
$ ansible -i contrib/terraform/openstack/hosts -m ping all
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

if you are deploying a system that needs bootstrapping, like Container Linux by CoreOS, these might have a state `FAILED` due to Container Linux by CoreOS not having python. As long as the state is not `UNREACHABLE`, this is fine.

if it fails try to connect manually via SSH ... it could be somthing as simple as a stale host key.

Deploy kubernetes:

```
$ ansible-playbook --become -i contrib/terraform/openstack/hosts cluster.yml
```

# clean up:

```
$ terraform destroy
Do you really want to destroy?
  Terraform will delete all your managed infrastructure.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
...
...
Apply complete! Resources: 0 added, 0 changed, 12 destroyed.
```
