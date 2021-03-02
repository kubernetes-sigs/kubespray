# Kubernetes on UpCloud with Terraform

Provision a Kubernetes cluster on [UpCloud](https://upcloud.com/) using Terraform and Kubespray

## Overview

The setup looks like following

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

## Requirements

* Terraform 0.12.0 or newer

## Quickstart

NOTE: Assumes you are at the root of the kubespray repo.

For authentication in your  cluster you can use the environment variables.
```bash
export UPCLOUD_USERNAME=username
export UPCLOUD_PASSWORD=password
```
To allow API access to your UpCloud account, you need to allow API connections by visiting [Account-page](https://hub.upcloud.com/account) in your UpCloud Hub.

Edit  `contrib/terraform/upcloud/cluster-settings.tfvars`  to match your requirement.

```bash
terraform apply --var-file \
 contrib/terraform/upcloud/cluster-settings.tfvars  \
    -state=tfstate-test.tfstate    \
     contrib/terraform/upcloud/
```

You should now have a inventory file named `inventory.ini` that you can use with kubespray.
