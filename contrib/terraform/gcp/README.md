# Kubernetes on GCP with Terraform

Provision a Kubernetes cluster on GCP using Terraform and Kubespray

## Overview

The setup looks like following

```text
                           Kubernetes cluster
                        +-----------------------+
+---------------+       |   +--------------+    |
|               |       |   | +--------------+  |
| API server LB +---------> | |              |  |
|               |       |   | | Master/etcd  |  |
+---------------+       |   | | node(s)      |  |
                        |   +-+              |  |
                        |     +--------------+  |
                        |           ^           |
                        |           |           |
                        |           v           |
+---------------+       |   +--------------+    |
|               |       |   | +--------------+  |
|  Ingress LB   +---------> | |              |  |
|               |       |   | |    Worker    |  |
+---------------+       |   | |    node(s)   |  |
                        |   +-+              |  |
                        |     +--------------+  |
                        +-----------------------+
```

## Requirements

* Terraform 0.12.0 or newer

## Quickstart

To get a cluster up and running you'll need a JSON keyfile.
Set the path to the file in the `tfvars.json` file and run the following:

```bash
terraform apply -var-file tfvars.json -state dev-cluster.tfstate -var gcp_project_id=<ID of your GCP project> -var keyfile_location=<location of the json keyfile>
```

To generate kubespray inventory based on the terraform state file you can run the following:

```bash
./generate-inventory.sh dev-cluster.tfstate > inventory.ini
```

You should now have a inventory file named `inventory.ini` that you can use with kubespray, e.g.

```bash
ansible-playbook -i contrib/terraform/gcp/inventory.ini cluster.yml -b -v
```

## Variables

### Required

* `keyfile_location`: Location to the keyfile to use as credentials for the google terraform provider
* `gcp_project_id`: ID of the GCP project to deploy the cluster in
* `ssh_pub_key`: Path to public ssh key to use for all machines
* `region`: The region where to run the cluster
* `machines`: Machines to provision. Key of this object will be used as the name of the machine
  * `node_type`: The role of this node *(master|worker)*
  * `size`: The size to use
  * `zone`: The zone the machine should run in
  * `additional_disks`: Extra disks to add to the machine. Key of this object will be used as the disk name
    * `size`: Size of the disk (in GB)
  * `boot_disk`: The boot disk to use
    * `image_name`: Name of the image
    * `size`: Size of the boot disk (in GB)
* `ssh_whitelist`: List of IP ranges (CIDR) that will be allowed to ssh to the nodes
* `api_server_whitelist`: List of IP ranges (CIDR) that will be allowed to connect to the API server
* `nodeport_whitelist`: List of IP ranges (CIDR) that will be allowed to connect to the kubernetes nodes on port 30000-32767 (kubernetes nodeports)
* `ingress_whitelist`: List of IP ranges (CIDR) that will be allowed to connect to ingress on ports 80 and 443
* `extra_ingress_firewalls`: Additional ingress firewall rules. Key will be used as the name of the rule
  * `source_ranges`: List of IP ranges (CIDR). Example: `["8.8.8.8"]`
  * `protocol`: Protocol. Example `"tcp"`
  * `ports`: List of ports, as string. Example `["53"]`
  * `target_tags`: List of target tag (either the machine name or `control-plane` or `worker`). Example: `["control-plane", "worker-0"]`

### Optional

* `prefix`: Prefix to use for all resources, required to be unique for all clusters in the same project *(Defaults to `default`)*
* `master_sa_email`: Service account email to use for the control plane nodes *(Defaults to `""`, auto generate one)*
* `master_sa_scopes`: Service account email to use for the control plane nodes *(Defaults to `["https://www.googleapis.com/auth/cloud-platform"]`)*
* `master_preemptible`: Enable [preemptible](https://cloud.google.com/compute/docs/instances/preemptible)
  for the control plane nodes *(Defaults to `false`)*
* `master_additional_disk_type`: [Disk type](https://cloud.google.com/compute/docs/disks/#disk-types)
  for extra disks added on the control plane nodes *(Defaults to `"pd-ssd"`)*
* `worker_sa_email`: Service account email to use for the worker nodes *(Defaults to `""`, auto generate one)*
* `worker_sa_scopes`: Service account email to use for the worker nodes *(Defaults to `["https://www.googleapis.com/auth/cloud-platform"]`)*
* `worker_preemptible`: Enable [preemptible](https://cloud.google.com/compute/docs/instances/preemptible)
  for the worker nodes *(Defaults to `false`)*
* `worker_additional_disk_type`: [Disk type](https://cloud.google.com/compute/docs/disks/#disk-types)
  for extra disks added on the worker nodes *(Defaults to `"pd-ssd"`)*

An example variables file can be found `tfvars.json`

## Known limitations

This solution does not provide a solution to use a bastion host. Thus all the nodes must expose a public IP for kubespray to work.
