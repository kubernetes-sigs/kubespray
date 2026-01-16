# Kubernetes on OpenStack with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
OpenStack.

## Status

This will install a Kubernetes cluster on an OpenStack Cloud. It should work on
most modern installs of OpenStack that support the basic services.

### Known compatible public clouds

- [Auro](https://auro.io/)
- [Betacloud](https://www.betacloud.io/)
- [CityCloud](https://www.citycloud.com/)
- [DreamHost](https://www.dreamhost.com/cloud/computing/)
- [ELASTX](https://elastx.se/)
- [EnterCloudSuite](https://www.entercloudsuite.com/)
- [FugaCloud](https://fuga.cloud/)
- [Open Telekom Cloud](https://cloud.telekom.de/)
- [OVH](https://www.ovh.com/)
- [Rackspace](https://www.rackspace.com/)
- [Safespring](https://www.safespring.com)
- [Ultimum](https://ultimum.io/)
- [VexxHost](https://vexxhost.com/)
- [Zetta](https://www.zetta.io/)
- [Cloudify](https://www.cloudify.ro/en)

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

#### Using an existing router

It is possible to use an existing router instead of creating one. To use an
existing router set the router\_id variable to the uuid of the router you wish
to use.

For example:

```ShellSession
router_id = "00c542e7-6f46-4535-ae95-984c7f0391a3"
```

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

### GlusterFS shared file system

The Terraform configuration supports provisioning of an optional GlusterFS
shared file system based on a separate set of VMs. To enable this, you need to
specify:

- the number of Gluster hosts (minimum 2)
- Size of the non-ephemeral volumes to be attached to store the GlusterFS bricks
- Other properties related to provisioning the hosts

Even if you are using Flatcar Container Linux by Kinvolk for your cluster, you will still
need the GlusterFS VMs to be based on either Debian or RedHat based images.
Flatcar Container Linux by Kinvolk cannot serve GlusterFS, but can connect to it through
binaries available on hyperkube v1.4.3_coreos.0 or higher.

## Requirements

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html) 0.14 or later
- [Install Ansible](http://docs.ansible.com/ansible/latest/intro_installation.html)
- you already have a suitable OS image in Glance
- you already have a floating IP pool created
- you have security groups enabled
- you have a pair of keys generated that can be used to secure the new hosts

## Module Architecture

The configuration is divided into four modules:

- Network
- Loadbalancer
- IPs
- Compute

The main reason for splitting the configuration up in this way is to easily
accommodate situations where floating IPs are limited by a quota or if you have
any external references to the floating IP (e.g. DNS) that would otherwise have
to be updated.

You can force your existing IPs by modifying the compute variables in
`kubespray.tf` as follows:

```ini
k8s_master_fips = ["151.101.129.67"]
k8s_node_fips = ["151.101.129.68"]
```

## Terraform

Terraform will be used to provision all of the OpenStack resources with base software as appropriate.

### Configuration

#### Inventory files

Create an inventory directory for your cluster by copying the existing sample and linking the `hosts` script (used to build the inventory based on Terraform state):

```ShellSession
cp -LRp contrib/terraform/openstack/sample-inventory inventory/$CLUSTER
cd inventory/$CLUSTER
ln -s ../../contrib/terraform/openstack/hosts
ln -s ../../contrib
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

- the current directory
- `~/.config/openstack`
- `/etc/openstack`

`clouds.yaml`:

```yaml
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

```ShellSession
export OS_CLOUD=mycloud
```

##### Openrc method

When using classic environment variables, Terraform uses default `OS_*`
environment variables.  A script suitable for your environment may be available
from Horizon under *Project* -> *Compute* -> *Access & Security* -> *API Access*.

With identity v2:

```ShellSession
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

```ShellSession
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

Terraform does not support a mix of DomainName and DomainID, choose one or the other:

- provider.openstack: You must provide exactly one of DomainID or DomainName to authenticate by Username

```ShellSession
unset OS_USER_DOMAIN_NAME
export OS_USER_DOMAIN_ID=default
```

or

```ShellSession
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
|`az_list` | List of Availability Zones available in your OpenStack cluster. |
|`network_name` | The name to be given to the internal network that will be generated |
|`use_existing_network`| Use an existing network with the name of `network_name`. `false` by default |
|`network_dns_domain` | (Optional) The dns_domain for the internal network that will be generated |
|`dns_nameservers`| An array of DNS name server names to be used by hosts in the internal subnet. |
|`floatingip_pool` | Name of the pool from which floating IPs will be allocated |
|`k8s_master_fips` | A list of floating IPs that you have already pre-allocated; they will be attached to master nodes instead of creating new random floating IPs. |
|`bastion_fips` | A list of floating IPs that you have already pre-allocated; they will be attached to bastion node instead of creating new random floating IPs. |
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
|`supplementary_master_groups` | To add ansible groups to the masters, such as `kube_node` for tainting them as nodes, empty by default. |
|`supplementary_node_groups` | To add ansible groups to the nodes, such as `kube_ingress` for running ingress controller pods, empty by default. |
|`bastion_allowed_remote_ips` | List of CIDR allowed to initiate a SSH connection, `["0.0.0.0/0"]` by default |
|`bastion_allowed_remote_ipv6_ips` | List of IPv6 CIDR allowed to initiate a SSH connection, `["::/0"]` by default |
|`master_allowed_remote_ips` | List of CIDR blocks allowed to initiate an API connection, `["0.0.0.0/0"]` by default |
|`master_allowed_remote_ipv6_ips` | List of IPv6 CIDR blocks allowed to initiate an API connection, `["::/0"]` by default |
|`bastion_allowed_ports` | List of ports to open on bastion node, `[]` by default |
|`bastion_allowed_ports_ipv6` | List of ports to open on bastion node for IPv6 CIDR blocks, `[]` by default |
|`k8s_allowed_remote_ips` | List of CIDR allowed to initiate a SSH connection, empty by default |
|`k8s_allowed_remote_ips_ipv6` | List of IPv6 CIDR allowed to initiate a SSH connection, empty by default |
|`k8s_allowed_egress_ipv6_ips` | List of IPv6 CIDRs allowed for egress traffic, `["::/0"]` by default |
|`worker_allowed_ports` | List of ports to open on worker nodes, `[{ "protocol" = "tcp", "port_range_min" = 30000, "port_range_max" = 32767, "remote_ip_prefix" = "0.0.0.0/0"}]` by default |
|`worker_allowed_ports_ipv6` | List of ports to open on worker nodes for IPv6 CIDR blocks, `[{ "protocol" = "tcp", "port_range_min" = 30000, "port_range_max" = 32767, "remote_ip_prefix" = "::/0"}]` by default |
|`master_allowed_ports` | List of ports to open on master nodes, expected format is `[{ "protocol" = "tcp", "port_range_min" = 443, "port_range_max" = 443, "remote_ip_prefix" = "0.0.0.0/0"}]`, empty by default |
|`master_allowed_ports_ipv6` | List of ports to open on master nodes for IPv6 CIDR blocks, expected format is `[{ "protocol" = "tcp", "port_range_min" = 443, "port_range_max" = 443, "remote_ip_prefix" = "::/0"}]`, empty by default |
|`node_root_volume_size_in_gb` | Size of the root volume for nodes, 0 to use ephemeral storage |
|`master_root_volume_size_in_gb` | Size of the root volume for masters, 0 to use ephemeral storage |
|`master_volume_type` | Volume type of the root volume for control_plane, 'Default' by default |
|`node_volume_type` | Volume type of the root volume for nodes, 'Default' by default |
|`gfs_root_volume_size_in_gb` | Size of the root volume for gluster, 0 to use ephemeral storage |
|`etcd_root_volume_size_in_gb` | Size of the root volume for etcd nodes, 0 to use ephemeral storage |
|`bastion_root_volume_size_in_gb` | Size of the root volume for bastions, 0 to use ephemeral storage |
|`master_server_group_policy` | Enable and use openstack nova servergroups for masters with set policy, default: "" (disabled) |
|`node_server_group_policy` | Enable and use openstack nova servergroups for nodes with set policy, default: "" (disabled) |
|`etcd_server_group_policy` | Enable and use openstack nova servergroups for etcd with set policy, default: "" (disabled) |
|`additional_server_groups` | Extra server groups to create. Set "policy" to the policy for the group, expected format is `{"new-server-group" = {"policy" = "anti-affinity"}}`, default: {} (to not create any extra groups) |
|`use_access_ip` | If 1, nodes with floating IPs will transmit internal cluster traffic via floating IPs; if 0 private IPs will be used instead. Default value is 1. |
|`port_security_enabled` | Allow to disable port security by setting this to `false`. `true` by default |
|`force_null_port_security` | Set `null` instead of `true` or `false` for `port_security`. `false` by default |
|`k8s_nodes` | Map containing worker node definition, see explanation below |
|`k8s_masters` | Map containing master node definition, see explanation for k8s_nodes and `sample-inventory/cluster.tfvars` |
| `k8s_master_loadbalancer_enabled`| Enable and use an Octavia load balancer for the K8s master nodes |
| `k8s_master_loadbalancer_listener_port` | Define via which port the K8s Api should be exposed. `6443` by default  |
| `k8s_master_loadbalancer_server_port` | Define via which port the K8S api is available on the mas. `6443` by default |
| `k8s_master_loadbalancer_public_ip` | Specify if an existing floating IP should be used for the load balancer. A new floating IP is assigned by default  |

##### k8s_nodes

Allows a custom definition of worker nodes giving the operator full control over individual node flavor and availability zone placement.
To enable the use of this mode set the `number_of_k8s_nodes` and `number_of_k8s_nodes_no_floating_ip` variables to 0.
Then define your desired worker node configuration using the `k8s_nodes` variable.
The `az`, `flavor` and `floating_ip` parameters are mandatory.
The optional parameter `extra_groups` (a comma-delimited string) can be used to define extra inventory group memberships for specific nodes.

```yaml
k8s_nodes:
   node-name:
    az: string # Name of the AZ
    flavor: string # Flavor ID to use
    floating_ip: bool # If floating IPs should be created or not
    extra_groups: string # (optional) Additional groups to add for kubespray, defaults to no groups
    image_id: string # (optional) Image ID to use, defaults to var.image_id or var.image
    root_volume_size_in_gb: number # (optional) Size of the block storage to use as root disk, defaults to var.node_root_volume_size_in_gb or to use volume from flavor otherwise
    volume_type: string # (optional) Volume type to use, defaults to var.node_volume_type
    network_id: string # (optional) Use this network_id for the node, defaults to either var.network_id or ID of var.network_name
    server_group: string # (optional) Server group to add this node to. If set, this has to be one specified in additional_server_groups, defaults to use the server group specified in node_server_group_policy
    cloudinit: # (optional) Options for cloud-init
      extra_partitions: # List of extra partitions (other than the root partition) to setup during creation
        volume_path: string # Path to the volume to create partition for (e.g. /dev/vda )
        partition_path: string # Path to the partition (e.g. /dev/vda2 )
        mount_path: string # Path to where the partition should be mounted
        partition_start: string # Where the partition should start (e.g. 10GB ). Note, if you set the partition_start to 0 there will be no space left for the root partition
        partition_end: string # Where the partition should end (e.g. 10GB or -1 for end of volume)
      netplan_critical_dhcp_interface: string # Name of interface to set the dhcp flag critical = true, to circumvent [this issue](https://bugs.launchpad.net/ubuntu/+source/systemd/+bug/1776013).
```

For example:

```ini
k8s_nodes = {
  "1" = {
    "az" = "sto1"
    "flavor" = "83d8b44a-26a0-4f02-a981-079446926445"
    "floating_ip" = true
  },
  "2" = {
    "az" = "sto2"
    "flavor" = "83d8b44a-26a0-4f02-a981-079446926445"
    "floating_ip" = true
  },
  "3" = {
    "az" = "sto3"
    "flavor" = "83d8b44a-26a0-4f02-a981-079446926445"
    "floating_ip" = true
    "extra_groups" = "calico_rr"
  }
}
```

Would result in the same configuration as:

```ini
number_of_k8s_nodes = 3
flavor_k8s_node = "83d8b44a-26a0-4f02-a981-079446926445"
az_list = ["sto1", "sto2", "sto3"]
```

And:

```ini
k8s_nodes = {
  "ing-1" = {
    "az" = "sto1"
    "flavor" = "83d8b44a-26a0-4f02-a981-079446926445"
    "floating_ip" = true
  },
  "ing-2" = {
    "az" = "sto2"
    "flavor" = "83d8b44a-26a0-4f02-a981-079446926445"
    "floating_ip" = true
  },
  "ing-3" = {
    "az" = "sto3"
    "flavor" = "83d8b44a-26a0-4f02-a981-079446926445"
    "floating_ip" = true
  },
  "big-1" = {
    "az" = "sto1"
    "flavor" = "3f73fc93-ec61-4808-88df-2580d94c1a9b"
    "floating_ip" = false
  },
  "big-2" = {
    "az" = "sto2"
    "flavor" = "3f73fc93-ec61-4808-88df-2580d94c1a9b"
    "floating_ip" = false
  },
  "big-3" = {
    "az" = "sto3"
    "flavor" = "3f73fc93-ec61-4808-88df-2580d94c1a9b"
    "floating_ip" = false
  },
  "small-1" = {
    "az" = "sto1"
    "flavor" = "7a6a998f-ac7f-4fb8-a534-2175b254f75e"
    "floating_ip" = false
  },
  "small-2" = {
    "az" = "sto2"
    "flavor" = "7a6a998f-ac7f-4fb8-a534-2175b254f75e"
    "floating_ip" = false
  },
  "small-3" = {
    "az" = "sto3"
    "flavor" = "7a6a998f-ac7f-4fb8-a534-2175b254f75e"
    "floating_ip" = false
  }
}
```

Would result in three nodes in each availability zone each with their own separate naming,
flavor and floating ip configuration.

The "schema":

```ini
k8s_nodes = {
  "key | node name suffix, must be unique" = {
    "az" = string
    "flavor" = string
    "floating_ip" = bool
  },
}
```

All values are required.

#### Terraform state files

In the cluster's inventory folder, the following files might be created (either by Terraform
or manually), to prevent you from pushing them accidentally they are in a
`.gitignore` file in the `terraform/openstack` directory :

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
terraform -chdir="../../contrib/terraform/openstack" init
```

This should finish fairly quickly telling you Terraform has successfully initialized and loaded necessary modules.

### Customizing with cloud-init

You can apply cloud-init based customization for the openstack instances before provisioning your cluster.
One common template is used for all instances. Adjust the file shown below:
`contrib/terraform/openstack/modules/compute/templates/cloudinit.yaml.tmpl`
For example, to enable openstack novnc access and ansible_user=root SSH access:

```ShellSession
#cloud-config
## in some cases novnc console access is required
## it requires ssh password to be set
ssh_pwauth: yes
chpasswd:
  list: |
    root:secret
  expire: False

## in some cases direct root ssh access via ssh key is required
disable_root: false
```

### Provisioning cluster

You can apply the Terraform configuration to your cluster with the following command
issued from your cluster's inventory directory (`inventory/$CLUSTER`):

```ShellSession
terraform -chdir="../../contrib/terraform/openstack" apply -var-file=cluster.tfvars
```

if you chose to create a bastion host, this script will create
`contrib/terraform/openstack/k8s_cluster.yml` with an ssh command for Ansible to
be able to access your machines tunneling through the bastion's IP address. If
you want to manually handle the ssh tunneling to these machines, please delete
or move that file. If you want to use this, just leave it there, as ansible will
pick it up automatically.

### Destroying cluster

You can destroy your new cluster with the following command issued from the cluster's inventory directory:

```ShellSession
terraform -chdir="../../contrib/terraform/openstack" destroy -var-file=cluster.tfvars
```

If you've started the Ansible run, it may also be a good idea to do some manual cleanup:

- remove SSH keys from the destroyed cluster from your `~/.ssh/known_hosts` file
- clean up any temporary cache files: `rm /tmp/$CLUSTER-*`

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

```ShellSession
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa
```

If you have deployed and destroyed a previous iteration of your cluster, you will need to clear out any stale keys from your SSH "known hosts" file ( `~/.ssh/known_hosts`).

#### Metadata variables

The [python script](../terraform.py) that reads the
generated`.tfstate` file to generate a dynamic inventory recognizes
some variables within a "metadata" block, defined in a "resource"
block (example):

```ini
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

### Configure cluster variables

Edit `inventory/$CLUSTER/group_vars/all/all.yml`:

- **bin_dir**:

```yml
# Directory where the binaries will be installed
# Default:
# bin_dir: /usr/local/bin
# For Flatcar Container Linux by Kinvolk:
bin_dir: /opt/bin
```

- and **cloud_provider**:

```yml
cloud_provider: openstack
```

Edit `inventory/$CLUSTER/group_vars/k8s_cluster/k8s_cluster.yml`:

- Set variable **kube_network_plugin** to your desired networking plugin.
  - **flannel** works out-of-the-box
  - **calico** requires [configuring OpenStack Neutron ports](/docs/cloud_providers/openstack.md) to allow service and pod subnets

```yml
# Choose network plugin (calico, weave or flannel)
# Can also be set to 'cloud', which lets the cloud provider setup appropriate routing
kube_network_plugin: flannel
```

- Set variable **resolvconf_mode**

```yml
# Can be docker_dns, host_resolvconf or none
# Default:
# resolvconf_mode: docker_dns
# For Flatcar Container Linux by Kinvolk:
resolvconf_mode: host_resolvconf
```

- Set max amount of attached cinder volume per host (default 256)

```yml
node_volume_attach_limit: 26
```

### Deploy Kubernetes

```ShellSession
ansible-playbook --become -i inventory/$CLUSTER/hosts cluster.yml
```

This will take some time as there are many tasks to run.

## Kubernetes

### Set up kubectl

1. [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) on your workstation
2. Add a route to the internal IP of a master node (if needed):

```ShellSession
sudo route add [master-internal-ip] gw [router-ip]
```

or

```ShellSession
sudo route add -net [internal-subnet]/24 gw [router-ip]
```

1. List Kubernetes certificates & keys:

```ShellSession
ssh [os-user]@[master-ip] sudo ls /etc/kubernetes/ssl/
```

1. Get `admin`'s certificates and keys:

```ShellSession
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-kube-master-1-key.pem > admin-key.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-kube-master-1.pem > admin.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/ca.pem > ca.pem
```

1. Configure kubectl:

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

1. Check it:

```ShellSession
kubectl version
```

## GlusterFS

GlusterFS is not deployed by the standard `cluster.yml` playbook, see the
[GlusterFS playbook documentation](../../network-storage/glusterfs/README.md)
for instructions.

Basically you will install Gluster as

```ShellSession
ansible-playbook --become -i inventory/$CLUSTER/hosts ./contrib/network-storage/glusterfs/glusterfs.yml
```

## What's next

Try out your new Kubernetes cluster with the [Hello Kubernetes service](https://kubernetes.io/docs/tasks/access-application-cluster/service-access-application-cluster/).

## Appendix

### Migration from `number_of_k8s_nodes*` to `k8s_nodes`

If you currently have a cluster defined using the `number_of_k8s_nodes*` variables and wish
to migrate to the `k8s_nodes` style you can do it like so:

```ShellSession
$ terraform state list
module.compute.data.openstack_images_image_v2.gfs_image
module.compute.data.openstack_images_image_v2.vm_image
module.compute.openstack_compute_floatingip_associate_v2.k8s_master[0]
module.compute.openstack_compute_floatingip_associate_v2.k8s_node[0]
module.compute.openstack_compute_floatingip_associate_v2.k8s_node[1]
module.compute.openstack_compute_floatingip_associate_v2.k8s_node[2]
module.compute.openstack_compute_instance_v2.k8s_master[0]
module.compute.openstack_compute_instance_v2.k8s_node[0]
module.compute.openstack_compute_instance_v2.k8s_node[1]
module.compute.openstack_compute_instance_v2.k8s_node[2]
module.compute.openstack_compute_keypair_v2.k8s
module.compute.openstack_compute_servergroup_v2.k8s_etcd[0]
module.compute.openstack_compute_servergroup_v2.k8s_master[0]
module.compute.openstack_compute_servergroup_v2.k8s_node[0]
module.compute.openstack_networking_secgroup_rule_v2.bastion[0]
module.compute.openstack_networking_secgroup_rule_v2.egress[0]
module.compute.openstack_networking_secgroup_rule_v2.k8s
module.compute.openstack_networking_secgroup_rule_v2.k8s_allowed_remote_ips[0]
module.compute.openstack_networking_secgroup_rule_v2.k8s_allowed_remote_ips[1]
module.compute.openstack_networking_secgroup_rule_v2.k8s_allowed_remote_ips[2]
module.compute.openstack_networking_secgroup_rule_v2.k8s_master[0]
module.compute.openstack_networking_secgroup_rule_v2.worker[0]
module.compute.openstack_networking_secgroup_rule_v2.worker[1]
module.compute.openstack_networking_secgroup_rule_v2.worker[2]
module.compute.openstack_networking_secgroup_rule_v2.worker[3]
module.compute.openstack_networking_secgroup_rule_v2.worker[4]
module.compute.openstack_networking_secgroup_v2.bastion[0]
module.compute.openstack_networking_secgroup_v2.k8s
module.compute.openstack_networking_secgroup_v2.k8s_master
module.compute.openstack_networking_secgroup_v2.worker
module.ips.null_resource.dummy_dependency
module.ips.openstack_networking_floatingip_v2.k8s_master[0]
module.ips.openstack_networking_floatingip_v2.k8s_node[0]
module.ips.openstack_networking_floatingip_v2.k8s_node[1]
module.ips.openstack_networking_floatingip_v2.k8s_node[2]
module.network.openstack_networking_network_v2.k8s[0]
module.network.openstack_networking_router_interface_v2.k8s[0]
module.network.openstack_networking_router_v2.k8s[0]
module.network.openstack_networking_subnet_v2.k8s[0]
$ terraform state mv 'module.compute.openstack_compute_floatingip_associate_v2.k8s_node[0]' 'module.compute.openstack_compute_floatingip_associate_v2.k8s_nodes["1"]'
Move "module.compute.openstack_compute_floatingip_associate_v2.k8s_node[0]" to "module.compute.openstack_compute_floatingip_associate_v2.k8s_nodes[\"1\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.compute.openstack_compute_floatingip_associate_v2.k8s_node[1]' 'module.compute.openstack_compute_floatingip_associate_v2.k8s_nodes["2"]'
Move "module.compute.openstack_compute_floatingip_associate_v2.k8s_node[1]" to "module.compute.openstack_compute_floatingip_associate_v2.k8s_nodes[\"2\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.compute.openstack_compute_floatingip_associate_v2.k8s_node[2]' 'module.compute.openstack_compute_floatingip_associate_v2.k8s_nodes["3"]'
Move "module.compute.openstack_compute_floatingip_associate_v2.k8s_node[2]" to "module.compute.openstack_compute_floatingip_associate_v2.k8s_nodes[\"3\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.compute.openstack_compute_instance_v2.k8s_node[0]' 'module.compute.openstack_compute_instance_v2.k8s_node["1"]'
Move "module.compute.openstack_compute_instance_v2.k8s_node[0]" to "module.compute.openstack_compute_instance_v2.k8s_node[\"1\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.compute.openstack_compute_instance_v2.k8s_node[1]' 'module.compute.openstack_compute_instance_v2.k8s_node["2"]'
Move "module.compute.openstack_compute_instance_v2.k8s_node[1]" to "module.compute.openstack_compute_instance_v2.k8s_node[\"2\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.compute.openstack_compute_instance_v2.k8s_node[2]' 'module.compute.openstack_compute_instance_v2.k8s_node["3"]'
Move "module.compute.openstack_compute_instance_v2.k8s_node[2]" to "module.compute.openstack_compute_instance_v2.k8s_node[\"3\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.ips.openstack_networking_floatingip_v2.k8s_node[0]' 'module.ips.openstack_networking_floatingip_v2.k8s_node["1"]'
Move "module.ips.openstack_networking_floatingip_v2.k8s_node[0]" to "module.ips.openstack_networking_floatingip_v2.k8s_node[\"1\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.ips.openstack_networking_floatingip_v2.k8s_node[1]' 'module.ips.openstack_networking_floatingip_v2.k8s_node["2"]'
Move "module.ips.openstack_networking_floatingip_v2.k8s_node[1]" to "module.ips.openstack_networking_floatingip_v2.k8s_node[\"2\"]"
Successfully moved 1 object(s).
$ terraform state mv 'module.ips.openstack_networking_floatingip_v2.k8s_node[2]' 'module.ips.openstack_networking_floatingip_v2.k8s_node["3"]'
Move "module.ips.openstack_networking_floatingip_v2.k8s_node[2]" to "module.ips.openstack_networking_floatingip_v2.k8s_node[\"3\"]"
Successfully moved 1 object(s).
```

Of course for nodes without floating ips those steps can be omitted.
