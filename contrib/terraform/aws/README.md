## Kubernetes on AWS with Terraform

**Overview:**

This project will create:
* VPC with Public and Private Subnets in # Availability Zones
* Bastion Hosts and NAT Gateways in the Public Subnet
* A dynamic number of masters, etcd, and worker nodes in the Private Subnet
 * even distributed over the # of Availability Zones
* AWS ELB in the Public Subnet for accessing the Kubernetes API from the internet

**Requirements**
- Terraform 0.8.7 or newer

**How to Use:**

- Export the variables for your AWS credentials or edit credentials.tfvars:

```
export aws_access_key="xxx"
export aws_secret_key="yyy"
export aws_ssh_key_name="zzz"
```

- Update contrib/terraform/aws/terraform.tfvars with your data

- Run with `terraform apply -var-file="credentials.tfvars"` or `terraform apply` depending if you exported your AWS credentials

- Once the infrastructure is created, you can run the kargo playbooks and supply inventory/hosts with the `-i` flag.

**Architecture**

Pictured is an AWS Infrastructure created with this Terraform project distributed over two Availability Zones.

![AWS Infrastructure with Terraform  ](docs/aws_kargo.png)
