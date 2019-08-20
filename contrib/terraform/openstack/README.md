# Kubernetes on Openstack with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
Openstack.

## Status

This will install a Kubernetes cluster on an Openstack Cloud. It should work on
most modern installs of OpenStack that support the basic services.

### Known compatible public clouds
- [Auro](https://auro.io/)
- [Betacloud](https://www.betacloud.io/)
- [CityCloud](https://www.citycloud.com/)
- [DreamHost](https://www.dreamhost.com/cloud/computing/)
- [ELASTX](https://elastx.se/)
- [EnterCloudSuite](https://www.entercloudsuite.com/)
- [FugaCloud](https://fuga.cloud/)
- [Open Telekom Cloud](https://cloud.telekom.de/) : requires to set the variable `wait_for_floatingip = "true"` in your cluster.tfvars
- [OVH](https://www.ovh.com/)
- [Rackspace](https://www.rackspace.com/)
- [Ultimum](https://ultimum.io/)
- [VexxHost](https://vexxhost.com/)
- [Zetta](https://www.zetta.io/)


## Approach
The terraform configuration inspects variables found in
[variables.tf](variables.tf) to create resources in your OpenStack cluster.
There is a [python script](../terraform.py) that reads the generated`.tfstate`
file to generate a dynamic inventory that is consumed by the main ansible script
to actually install kubernetes and stand up the cluster.

### Networking
The configuration includes creating a private subnet with a router to the
external net. It will allocate floating IPs from a pool and assign them to the
hosts where that makes sense. You have the option of creating bastion hosts
inside the private subnet to access the nodes there.  Alternatively, a node with
a floating IP can be used as a jump host to nodes without.

### Kubernetes Nodes
You can create many different kubernetes topologies by setting the number of
different classes of hosts. For each class there are options for allocating
floating IP addresses or not.
- Master nodes with etcd
- Master nodes without etcd
- Standalone etcd hosts
- Kubernetes worker nodes

Note that the Ansible script will report an invalid configuration if you wind up
with an even number of etcd instances since that is not a valid configuration. This
restriction includes standalone etcd nodes that are deployed in a cluster along with
master nodes with etcd replicas. As an example, if you have three master nodes with
etcd replicas and three standalone etcd nodes, the script will fail since there are
now six total etcd replicas.

### GlusterFS
The Terraform configuration supports provisioning of an optional GlusterFS
shared file system based on a separate set of VMs. To enable this, you need to
specify:
- the number of Gluster hosts (minimum 2)
- Size of the non-ephemeral volumes to be attached to store the GlusterFS bricks
- Other properties related to provisioning the hosts

Even if you are using Container Linux by CoreOS for your cluster, you will still
need the GlusterFS VMs to be based on either Debian or RedHat based images.
Container Linux by CoreOS cannot serve GlusterFS, but can connect to it through
binaries available on hyperkube v1.4.3_coreos.0 or higher.

## Requirements

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html) 0.12 or later
- [Install Ansible](http://docs.ansible.com/ansible/latest/intro_installation.html)
- you already have a suitable OS image in Glance
- you already have a floating IP pool created
- you have security groups enabled
- you have a pair of keys generated that can be used to secure the new hosts

## Module Architecture
The configuration is divided into three modules:
- Network
- IPs
- Compute

The main reason for splitting the configuration up in this way is to easily
accommodate situations where floating IPs are limited by a quota or if you have
any external references to the floating IP (e.g. DNS) that would otherwise have
to be updated.

You can force your existing IPs by modifying the compute variables in
`kubespray.tf` as follows:

```
k8s_master_fips = ["151.101.129.67"]
k8s_node_fips = ["151.101.129.68"]
```

## Terraform
Terraform will be used to provision all of the OpenStack resources with base software as appropriate.

### Configuration

#### Inventory files

Create an inventory directory for your cluster by copying the existing sample and linking the `hosts` script (used to build the inventory based on Terraform state):

```ShellSession
$ cp -LRp contrib/terraform/openstack/sample-inventory inventory/$CLUSTER
$ cd inventory/$CLUSTER
$ ln -s ../../contrib/terraform/openstack/hosts
$ ln -s ../../contrib
```

This will be the base for subsequent Terraform commands.

#### OpenStack access and credentials

No provider variables are hardcoded inside `variables.tf` because Terraform
supports various authentication methods for OpenStack: the older script and
environment method (using `openrc`) as well as a newer declarative method, and
different OpenStack environments may support Identity API version 2 or 3.

These are examples and may vary depending on your OpenStack cloud provider,
for an exhaustive list on how to authenticate on OpenStack with Terraform
please read the [OpenStack provider documentation](https://www.terraform.io/docs/providers/openstack/).

##### Declarative method (recommended)

The recommended authentication method is to describe credentials in a YAML file `clouds.yaml` that can be stored in:

* the current directory
* `~/.config/openstack`
* `/etc/openstack`

`clouds.yaml`:

```
clouds:
  mycloud:
    auth:
      auth_url: https://openstack:5000/v3
      username: "username"
      project_name: "projectname"
      project_id: projectid
      user_domain_name: "Default"
      password: "password"
    region_name: "RegionOne"
    interface: "public"
    identity_api_version: 3
```

If you have multiple clouds defined in your `clouds.yaml` file you can choose
the one you want to use with the environment variable `OS_CLOUD`:

```
export OS_CLOUD=mycloud
```

##### Openrc method

When using classic environment variables, Terraform uses default `OS_*`
environment variables.  A script suitable for your environment may be available
from Horizon under *Project* -> *Compute* -> *Access & Security* -> *API Access*.

With identity v2:

```
source openrc

env | grep OS

OS_AUTH_URL=https://openstack:5000/v2.0
OS_PROJECT_ID=projectid
OS_PROJECT_NAME=projectname
OS_USERNAME=username
OS_PASSWORD=password
OS_REGION_NAME=RegionOne
OS_INTERFACE=public
OS_IDENTITY_API_VERSION=2
```

With identity v3:

```
source openrc

env | grep OS

OS_AUTH_URL=https://openstack:5000/v3
OS_PROJECT_ID=projectid
OS_PROJECT_NAME=username
OS_PROJECT_DOMAIN_ID=default
OS_USERNAME=username
OS_PASSWORD=password
OS_REGION_NAME=RegionOne
OS_INTERFACE=public
OS_IDENTITY_API_VERSION=3
OS_USER_DOMAIN_NAME=Default
```

Terraform does not support a mix of DomainName and DomainID, choose one or the
other:

```
* provider.openstack: You must provide exactly one of DomainID or DomainName to authenticate by Username
```

```
unset OS_USER_DOMAIN_NAME
export OS_USER_DOMAIN_ID=default

or

unset OS_PROJECT_DOMAIN_ID
set OS_PROJECT_DOMAIN_NAME=Default
```

#### Cluster variables
The construction of the cluster is driven by values found in
[variables.tf](variables.tf).

For your cluster, edit `inventory/$CLUSTER/cluster.tfvars`.

|Variable | Description |
|---------|-------------|
|`cluster_name` | All OpenStack resources will use the Terraform variable`cluster_name` (default`example`) in their name to make it easier to track. For example the first compute resource will be named`example-kubernetes-1`. |
|`network_name` | The name to be given to the internal network that will be generated |
|`dns_nameservers`| An array of DNS name server names to be used by hosts in the internal subnet. |
|`floatingip_pool` | Name of the pool from which floating IPs will be allocated |
|`external_net` | UUID of the external network that will be routed to |
|`flavor_k8s_master`,`flavor_k8s_node`,`flavor_etcd`, `flavor_bastion`,`flavor_gfs_node` | Flavor depends on your openstack installation, you can get available flavor IDs through `openstack flavor list` |
|`image`,`image_gfs` | Name of the image to use in provisioning the compute resources. Should already be loaded into glance. |
|`ssh_user`,`ssh_user_gfs` | The username to ssh into the image with. This usually depends on the image you have selected |
|`public_key_path` | Path on your local workstation to the public key file you wish to use in creating the key pairs |
|`number_of_k8s_masters`, `number_of_k8s_masters_no_floating_ip` | Number of nodes that serve as both master and etcd. These can be provisioned with or without floating IP addresses|
|`number_of_k8s_masters_no_etcd`, `number_of_k8s_masters_no_floating_ip_no_etcd` |  Number of nodes that serve as just master with no etcd. These can be provisioned with or without floating IP addresses |
|`number_of_etcd` | Number of pure etcd nodes |
|`number_of_k8s_nodes`, `number_of_k8s_nodes_no_floating_ip` | Kubernetes worker nodes. These can be provisioned with or without floating ip addresses. |
|`number_of_bastions` | Number of bastion hosts to create. Scripts assume this is really just zero or one |
|`number_of_gfs_nodes_no_floating_ip` | Number of gluster servers to provision. |
| `gfs_volume_size_in_gb` | Size of the non-ephemeral volumes to be attached to store the GlusterFS bricks |
|`supplementary_master_groups` | To add ansible groups to the masters, such as `kube-node` for tainting them as nodes, empty by default. |
|`supplementary_node_groups` | To add ansible groups to the nodes, such as `kube-ingress` for running ingress controller pods, empty by default. |
|`bastion_allowed_remote_ips` | List of CIDR allowed to initiate a SSH connection, `["0.0.0.0/0"]` by default |
|`master_allowed_remote_ips` | List of CIDR blocks allowed to initiate an API connection, `["0.0.0.0/0"]` by default |
|`k8s_allowed_remote_ips` | List of CIDR allowed to initiate a SSH connection, empty by default |
|`worker_allowed_ports` | List of ports to open on worker nodes, `[{ "protocol" = "tcp", "port_range_min" = 30000, "port_range_max" = 32767, "remote_ip_prefix" = "0.0.0.0/0"}]` by default |
|`wait_for_floatingip` | Let Terraform poll the instance until the floating IP has been associated, `false` by default. |

#### Terraform state files

In the cluster's inventory folder, the following files might be created (either by Terraform
or manually), to prevent you from pushing them accidentally they are in a
`.gitignore` file in the `terraform/openstack` directory :

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
$ terraform init ../../contrib/terraform/openstack
```

This should finish fairly quickly telling you Terraform has successfully initialized and loaded necessary modules.

### Provisioning cluster
You can apply the Terraform configuration to your cluster with the following command
issued from your cluster's inventory directory (`inventory/$CLUSTER`):
```ShellSession
$ terraform apply -var-file=cluster.tfvars ../../contrib/terraform/openstack
```

if you chose to create a bastion host, this script will create
`contrib/terraform/openstack/k8s-cluster.yml` with an ssh command for Ansible to
be able to access your machines tunneling through the bastion's IP address. If
you want to manually handle the ssh tunneling to these machines, please delete
or move that file. If you want to use this, just leave it there, as ansible will
pick it up automatically.

### Destroying cluster
You can destroy your new cluster with the following command issued from the cluster's inventory directory:

```ShellSession
$ terraform destroy -var-file=cluster.tfvars ../../contrib/terraform/openstack
```

If you've started the Ansible run, it may also be a good idea to do some manual cleanup:

* remove SSH keys from the destroyed cluster from your `~/.ssh/known_hosts` file
* clean up any temporary cache files: `rm /tmp/$CLUSTER-*`

### Debugging
You can enable debugging output from Terraform by setting
`OS_DEBUG` to 1 and`TF_LOG` to`DEBUG` before running the Terraform command.

### Terraform output

Terraform can output values that are useful for configure Neutron/Octavia LBaaS or Cinder persistent volume provisioning as part of your Kubernetes deployment:

 - `private_subnet_id`: the subnet where your instances are running is used for `openstack_lbaas_subnet_id`
 - `floating_network_id`: the network_id where the floating IP are provisioned is used for `openstack_lbaas_floating_network_id`

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

#### Metadata variables

The [python script](../terraform.py) that reads the
generated`.tfstate` file to generate a dynamic inventory recognizes
some variables within a "metadata" block, defined in a "resource"
block (example):

```
resource "openstack_compute_instance_v2" "example" {
    ...
    metadata {
        ssh_user = "ubuntu"
        prefer_ipv6 = true
	python_bin = "/usr/bin/python3"
    }
    ...
}
```

As the example shows, these let you define the SSH username for
Ansible, a Python binary which is needed by Ansible if
`/usr/bin/python` doesn't exist, and whether the IPv6 address of the
instance should be preferred over IPv4.

#### Bastion host

Bastion access will be determined by:

 - Your choice on the amount of bastion hosts (set by `number_of_bastions` terraform variable).
 - The existence of nodes/masters with floating IPs (set by `number_of_k8s_masters`, `number_of_k8s_nodes`, `number_of_k8s_masters_no_etcd` terraform variables).

If you have a bastion host, your ssh traffic will be directly routed through it. This is regardless of whether you have masters/nodes with a floating IP assigned.
If you don't have a bastion host, but at least one of your masters/nodes have a floating IP, then ssh traffic will be tunneled by one of these machines.

So, either a bastion host, or at least master/node with a floating IP are required.

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

### Configure cluster variables

Edit `inventory/$CLUSTER/group_vars/all/all.yml`:
- **bin_dir**:
```
# Directory where the binaries will be installed
# Default:
# bin_dir: /usr/local/bin
# For Container Linux by CoreOS:
bin_dir: /opt/bin
```
- and **cloud_provider**:
```
cloud_provider: openstack
```
Edit `inventory/$CLUSTER/group_vars/k8s-cluster/k8s-cluster.yml`:
- Set variable **kube_network_plugin** to your desired networking plugin.
  - **flannel** works out-of-the-box
  - **calico** requires [configuring OpenStack Neutron ports](/docs/openstack.md) to allow service and pod subnets
```
# Choose network plugin (calico, weave or flannel)
# Can also be set to 'cloud', which lets the cloud provider setup appropriate routing
kube_network_plugin: flannel
```
- Set variable **resolvconf_mode**
```
# Can be docker_dns, host_resolvconf or none
# Default:
# resolvconf_mode: docker_dns
# For Container Linux by CoreOS:
resolvconf_mode: host_resolvconf
```
- Set max amount of attached cinder volume per host (default 256)
```
node_volume_attach_limit: 26
```


### Deploy Kubernetes

```
$ ansible-playbook --become -i inventory/$CLUSTER/hosts cluster.yml
```

This will take some time as there are many tasks to run.

## Kubernetes

### Set up kubectl
1. [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) on your workstation
2. Add a route to the internal IP of a master node (if needed):
```
sudo route add [master-internal-ip] gw [router-ip]
```
or
```
sudo route add -net [internal-subnet]/24 gw [router-ip]
```
3. List Kubernetes certificates & keys:
```
ssh [os-user]@[master-ip] sudo ls /etc/kubernetes/ssl/
```
4. Get `admin`'s certificates and keys:
```
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-kube-master-1-key.pem > admin-key.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-kube-master-1.pem > admin.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/ca.pem > ca.pem
```
5. Configure kubectl:
```ShellSession
$ kubectl config set-cluster default-cluster --server=https://[master-internal-ip]:6443 \
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

## GlusterFS
GlusterFS is not deployed by the standard`cluster.yml` playbook, see the
[GlusterFS playbook documentation](../../network-storage/glusterfs/README.md)
for instructions.

Basically you will install Gluster as
```ShellSession
$ ansible-playbook --become -i inventory/$CLUSTER/hosts ./contrib/network-storage/glusterfs/glusterfs.yml
```


## What's next

Try out your new Kubernetes cluster with the [Hello Kubernetes service](https://kubernetes.io/docs/tasks/access-application-cluster/service-access-application-cluster/).
