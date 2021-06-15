# Kubernetes on Exoscale with Terraform

Provision a Kubernetes cluster on [vSphere](https://www.vmware.com/se/products/vsphere.html) using Terraform and Kubespray.

## Overview

The setup looks like following.

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

## Warning

This setup assumes that the DHCP is disabled in the vSphere cluster and IP addresses have to be provided in the configuration file.

## Requirements

* Terraform 0.13.0 or newer

*0.12 also works if you modify the provider block to include version and remove all `versions.tf` files*

## Quickstart

NOTE: *Assumes you are at the root of the kubespray repo*

Copy the sample inventory for your cluster and copy the default terraform variables.

```bash
CLUSTER=my-vsphere-cluster
cp -r inventory/sample inventory/$CLUSTER
cp contrib/terraform/vsphere/default.tfvars inventory/$CLUSTER/
cd inventory/$CLUSTER
```

Edit `default.tfvars` to match your setup. You MUST set values specific for you network and vSphere cluster.

```bash
# Ensure $EDITOR points to your favorite editor, e.g., vim, emacs, VS Code, etc.
$EDITOR default.tfvars
```

For authentication in your vSphere cluster you can use the environment variables.

```bash
export TF_VAR_vsphere_user=username
export TF_VAR_vsphere_password=password
```

Run Terraform to create the infrastructure.

```bash
terraform init ../../contrib/terraform/vsphere
terraform apply \
    -var-file default.tfvars \
    -state=tfstate-$CLUSTER.tfstate \
    ../../contrib/terraform/vsphere
```

You should now have a inventory file named `inventory.ini` that you can use with kubespray.
You can now copy your inventory file and use it with kubespray to set up a cluster.
You can type `terraform output` to find out the IP addresses of the nodes.

It is a good idea to check that you have basic SSH connectivity to the nodes. You can do that by:

```bash
ansible -i inventory.ini -m ping all
```

Example to use this with the default sample inventory:

```bash
ansible-playbook -i inventory.ini ../../cluster.yml -b -v
```

## Variables

### Required

* `machines`: Machines to provision. Key of this object will be used as the name of the machine
  * `node_type`: The role of this node *(master|worker)*
  * `ip`: The IP address with the netmask (CIDR notation)
* `gateway`: The IP address of the network gateway
* `ssh_public_keys`: List of public SSH keys to install on all machines
* `vsphere_datacenter`: The identifier of vSphere data center
* `vsphere_compute_cluster`: The identifier of vSphere compute cluster
* `vsphere_datastore`: The identifier of vSphere data store
* `vsphere_server`: The address of vSphere server
* `vsphere_hostname`: The IP address of vSphere hostname
* `template_name`: The name of a base image (the image has to be uploaded to vSphere beforehand)

### Optional

* `prefix`: Prefix to use for all resources, required to be unique for all clusters in the same project *(Defaults to `default`)*
* `dns_primary`: The IP address of primary DNS server *(Defaults to `8.8.4.4`)*
* `dns_secondary`:The IP address of secondary DNS server *(Defaults to `8.8.8.8`)*

An example variables file can be found `default.tfvars`
