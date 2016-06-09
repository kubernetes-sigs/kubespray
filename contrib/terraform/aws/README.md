## Kubernetes on AWS with Terraform

**Overview:**

- This will create nodes in a VPC inside of AWS

- A dynamic number of masters, etcd, and nodes can be created

- These scripts currently expect Private IP connectivity with the nodes that are created. This means that you may need a tunnel to your VPC or to run these scripts from a VM inside the VPC. Will be looking into how to work around this later.

**How to Use:**

- Export the variables for your Amazon credentials:

```
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="yyy"
```

- Update contrib/terraform/aws/terraform.tfvars with your data

- Run with `terraform apply`

- Once the infrastructure is created, you can run the kubespray playbooks and supply contrib/terraform/aws/inventory with the `-i` flag.

**Future Work:**

- Update the inventory creation file to be something a little more reasonable. It's just a local-exec from Terraform now, using terraform.py or something may make sense in the future.