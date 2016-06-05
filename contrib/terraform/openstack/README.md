# Kubernetes on Openstack with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
Openstack.

## Status

This will install a Kubernetes cluster on an Openstack Cloud. It is tested on a
OpenStack Cloud provided by [BlueBox](https://www.blueboxcloud.com/) and
should work on most modern installs of OpenStack that support the basic
services.

There are some assumptions made to try and ensure it will work on your openstack cluster.

* floating-ips are used for access
* you already have a suitable OS image in glance
* you already have both an internal network and a floating-ip pool created
* you have security-groups enabled


## Requirements

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html)

## Terraform

Terraform will be used to provision all of the OpenStack resources required to
run Docker Swarm.   It is also used to deploy and provision the software
requirements.

### Prep

#### OpenStack

Ensure your OpenStack credentials are loaded in environment variables. This is
how I do it:

```
$ source ~/.stackrc
```

You will need two networks before installing, an internal network and 
an external (floating IP Pool) network. The internet network can be shared as
we use security groups to provide network segregation. Due to the many
differences between OpenStack installs the Terraform does not attempt to create
these for you.

By default Terraform will expect that your networks are called `internal` and
`external`. You can change this by altering the Terraform variables `network_name` and `floatingip_pool`.

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

# Provision a Kubernetes Cluster on OpenStack

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
