# Kubernetes on Openstack with Terraform

Provision a Kubernetes cluster with [Terraform](https://www.terraform.io) on
Openstack.

## Status

This will install a Kubernetes cluster on an Openstack Cloud. It should work on
most modern installs of OpenStack that support the basic services.

## Approach
The terraform configuration inspects variables found in
[variables.tf](variables.tf) to create resources in your OpenStack cluster.
There is a [python script](../terraform.py) that reads the generated`.tfstate`
file to generate a dynamic inventory that is consumed by the main ansible script
to actually install kubernetes and stand up the cluster.

### Networking
The configuration includes creating a private subnet with a router to the
external net. It will allocate floating-ips from a pool and assign them to the
hosts where that makes sense. You have the option of creating bastion hosts
inside the private subnet to access the nodes there.

### Kubernetes Nodes
You can create many different kubernetes topologies by setting the number of
different classes of hosts. For each class there are options for allocating
floating ip addresses or not.
- Master Nodes with etcd
- Master nodes without etcd
- Standalone etcd hosts
- Kubernetes worker nodes

Note that the ansible script will report an invalid configuration if you wind up
with an even number of etcd instances since that is not a valid configuration.

### Gluster FS
The terraform configuration supports provisioning of an optional GlusterFS
shared file system based on a separate set of VMs. To enable this, you need to
specify
- the number of gluster hosts
- Size of the non-ephemeral volumes to be attached to store the GlusterFS bricks
- Other properties related to provisioning the hosts

Even if you are using Container Linux by CoreOS for your cluster, you will still
need the GlusterFS VMs to be based on either Debian or RedHat based images,
Container Linux by CoreOS cannot serve GlusterFS, but can connect to it through
binaries available on hyperkube v1.4.3_coreos.0 or higher.

## Requirements

- [Install Terraform](https://www.terraform.io/intro/getting-started/install.html)
- [Install Ansible](http://docs.ansible.com/ansible/latest/intro_installation.html)
- you already have a suitable OS image in glance
- you already have a floating-ip pool created
- you have security-groups enabled
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
`kubespray.tf` as

```
k8s_master_fips = ["151.101.129.67"]
k8s_node_fips = ["151.101.129.68"]
```

## Terraform
Terraform will be used to provision all of the OpenStack resources. It is also
used to deploy and provision the software requirements.

### Prep

#### OpenStack

No provider variables are hard coded inside `variables.tf` because Terraform
supports various authentication method for OpenStack, between identity v2 and
v3 API, `openrc` or `clouds.yaml`.

These are examples and may vary depending on your OpenStack cloud provider,
for an exhaustive list on how to authenticate on OpenStack with Terraform
please read the [OpenStack provider documentation](https://www.terraform.io/docs/providers/openstack/).

##### Recommended method : clouds.yaml

Newer recommended authentication method is to use a `clouds.yaml` file that can be store in :

* `Current Directory`
* `~/.config/openstack`
* `/etc/openstack`

`clouds.yaml` :

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
the one you want to use with the environment variable `OS_CLOUD` :

```
export OS_CLOUD=mycloud
```

##### Deprecated method : openrc

When using classic environment variables, Terraform uses default `OS_*`
environment variables :

With identity v2 :

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

With identity v3 :

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
other :

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

### Terraform Variables
The construction of the cluster is driven by values found in
[variables.tf](variables.tf).

The best way to set these values is to create a file in the project's root
directory called something like`my-terraform-vars.tfvars`. Many of the
variables are obvious. Here is a summary of some of the more interesting
ones:

|Variable | Description |
|---------|-------------|
|`cluster_name` | All OpenStack resources will use the Terraform variable`cluster_name` (default`example`) in their name to make it easier to track. For example the first compute resource will be named`example-kubernetes-1`. |
|`network_name` | The name to be given to the internal network that will be generated |
|`dns_nameservers`| An array of DNS name server names to be used by hosts in the internal subnet. |
|`floatingip_pool` | Name of the pool from which floating IPs will be allocated |
|`external_net` | UUID of the external network that will be routed to |
|`flavor_k8s_master`,`flavor_k8s_node`,`flavor_etcd`, `flavor_bastion`,`flavor_gfs_node` | Flavor depends on your openstack installation, you can get available flavor IDs through`nova flavor-list` |
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

### Terraform files

In the root folder, the following files might be created (either by Terraform
or manually), to prevent you from pushing them accidentally they are in a
`.gitignore` file in the `terraform/openstack` directory :

* `.terraform`
* `.tfvars`
* `.tfstate`
* `.tfstate.backup`

You can still add them manually if you want to.

## Initializing Terraform

Before Terraform can operate on your cluster you need to install required
plugins. This is accomplished with the command

```bash
$ terraform init contrib/terraform/openstack
```

## Provisioning Cluster with Terraform
You can apply the terraform config to your cluster with the following command
issued from the project's root directory
```bash
$ terraform apply -state=contrib/terraform/openstack/terraform.tfstate -var-file=my-terraform-vars.tfvars contrib/terraform/openstack
```

if you chose to create a bastion host, this script will create
`contrib/terraform/openstack/k8s-cluster.yml` with an ssh command for ansible to
be able to access your machines tunneling  through the bastion's ip adress. If
you want to manually handle the ssh tunneling to these machines, please delete
or move that file. If you want to use this, just leave it there, as ansible will
pick it up automatically.


## Destroying Cluster with Terraform
You can destroy a config deployed to your cluster with the following command
issued from the project's root directory
```bash
$ terraform destroy -state=contrib/terraform/openstack/terraform.tfstate -var-file=my-terraform-vars.tfvars contrib/terraform/openstack
```

## Debugging Cluster Provisioning
You can enable debugging output from Terraform by setting
`OS_DEBUG` to 1 and`TF_LOG` to`DEBUG` before runing the terraform command

## Terraform output

Terraform can output useful values that need to be reused if you want to use Kubernetes OpenStack cloud provider with Neutron/Octavia LBaaS or Cinder persistent Volume provisioning:

 - `private_subnet_id`: the subnet where your instances are running, maps to `openstack_lbaas_subnet_id`
 - `floating_network_id`: the network_id where the floating IP are provisioned, maps to `openstack_lbaas_floating_network_id`

# Running the Ansible Script
Ensure your local ssh-agent is running and your ssh key has been added. This
step is required by the terraform provisioner:

```
$ eval $(ssh-agent -s)
$ ssh-add ~/.ssh/id_rsa
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

if you are deploying a system that needs bootstrapping, like Container Linux by
CoreOS, these might have a state`FAILED` due to Container Linux by CoreOS not
having python. As long as the state is not`UNREACHABLE`, this is fine.

if it fails try to connect manually via SSH ... it could be something as simple as a stale host key.

## Configure Cluster variables

Edit `inventory/sample/group_vars/all.yml`:
- Set variable **bootstrap_os** according selected image
```
# Valid bootstrap options (required): ubuntu, coreos, centos, none
bootstrap_os: coreos
```
- **bin_dir**
```
# Directory where the binaries will be installed
# Default:
# bin_dir: /usr/local/bin
# For Container Linux by CoreOS:
bin_dir: /opt/bin
```
- and **cloud_provider**
```
cloud_provider: openstack
```
Edit `inventory/sample/group_vars/k8s-cluster.yml`:
- Set variable **kube_network_plugin** according selected networking
```
# Choose network plugin (calico, weave or flannel)
# Can also be set to 'cloud', which lets the cloud provider setup appropriate routing
kube_network_plugin: flannel
```
> flannel works out-of-the-box

> calico requires allowing service's and pod's subnets on according OpenStack Neutron ports
- Set variable **resolvconf_mode**
```
# Can be docker_dns, host_resolvconf or none
# Default:
# resolvconf_mode: docker_dns
# For Container Linux by CoreOS:
resolvconf_mode: host_resolvconf
```

For calico configure OpenStack Neutron ports: [OpenStack](/docs/openstack.md)

## Deploy kubernetes:

```
$ ansible-playbook --become -i contrib/terraform/openstack/hosts cluster.yml
```

## Set up local kubectl
1. Install kubectl on your workstation:
[Install and Set Up kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
2. Add route to internal IP of master node (if needed):
```
sudo route add [master-internal-ip] gw [router-ip]
```
or
```
sudo route add -net [internal-subnet]/24 gw [router-ip]
```
3. List Kubernetes certs&keys:
```
ssh [os-user]@[master-ip] sudo ls /etc/kubernetes/ssl/
```
4. Get admin's certs&key:
```
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-[cluster_name]-k8s-master-1-key.pem > admin-key.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/admin-[cluster_name]-k8s-master-1.pem > admin.pem
ssh [os-user]@[master-ip] sudo cat /etc/kubernetes/ssl/ca.pem > ca.pem
```
5. Configure kubectl:
```
kubectl config set-cluster default-cluster --server=https://[master-internal-ip]:6443 \
    --certificate-authority=ca.pem

kubectl config set-credentials default-admin \
    --certificate-authority=ca.pem \
    --client-key=admin-key.pem \
    --client-certificate=admin.pem

kubectl config set-context default-system --cluster=default-cluster --user=default-admin
kubectl config use-context default-system
```
7. Check it:
```
kubectl version
```

If you are using floating ip addresses then you may get this error:
```
Unable to connect to the server: x509: certificate is valid for 10.0.0.6, 10.0.0.6, 10.233.0.1, 127.0.0.1, not 132.249.238.25
```

You can tell kubectl to ignore this condition by adding the
`--insecure-skip-tls-verify` option.

## GlusterFS
GlusterFS is not deployed by the standard`cluster.yml` playbook, see the
[glusterfs playbook documentation](../../network-storage/glusterfs/README.md)
for instructions.

Basically you will install gluster as
```bash
$ ansible-playbook --become -i contrib/terraform/openstack/hosts ./contrib/network-storage/glusterfs/glusterfs.yml
```


# What's next
[Start Hello Kubernetes Service](https://kubernetes.io/docs/tasks/access-application-cluster/service-access-application-cluster/)
