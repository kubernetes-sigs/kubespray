# AWS

To deploy kubespray on [AWS](https://aws.amazon.com/) uncomment the `cloud_provider` option in `group_vars/all.yml` and set it to `'aws'`. Refer to the [Kubespray Configuration](#kubespray-configuration) for customizing the provider.

Prior to creating your instances, you **must** ensure that you have created IAM roles and policies for both "kubernetes-master" and "kubernetes-node". You can find the IAM policies [here](https://github.com/kubernetes-sigs/kubespray/tree/master/contrib/aws_iam/). See the [IAM Documentation](https://aws.amazon.com/documentation/iam/) if guidance is needed on how to set these up. When you bring your instances online, associate them with the respective IAM role. Nodes that are only to be used for Etcd do not need a role.

You would also need to tag the resources in your VPC accordingly for the aws provider to utilize them. Tag the subnets, route tables and all instances that kubernetes will be run on with key `kubernetes.io/cluster/$cluster_name` (`$cluster_name` must be a unique identifier for the cluster). Tag the subnets that must be targeted by external ELBs with the key `kubernetes.io/role/elb` and internal ELBs with the key `kubernetes.io/role/internal-elb`.

Make sure your VPC has both DNS Hostnames support and Private DNS enabled.

The next step is to make sure the hostnames in your `inventory` file are identical to your internal hostnames in AWS. This may look something like `ip-111-222-333-444.us-west-2.compute.internal`. You can then specify how Ansible connects to these instances with `ansible_ssh_host` and `ansible_ssh_user`.

You can now create your cluster!

## Dynamic Inventory

There is also a dynamic inventory script for AWS that can be used if desired. However, be aware that it makes some certain assumptions about how you'll create your inventory. It also does not handle all use cases and groups that we may use as part of more advanced deployments. Additions welcome.

This will produce an inventory that is passed into Ansible that looks like the following:

```json
{
  "_meta": {
    "hostvars": {
      "ip-172-31-3-xxx.us-east-2.compute.internal": {
        "ansible_ssh_host": "172.31.3.xxx"
      },
      "ip-172-31-8-xxx.us-east-2.compute.internal": {
        "ansible_ssh_host": "172.31.8.xxx"
      }
    }
  },
  "etcd": [
    "ip-172-31-3-xxx.us-east-2.compute.internal"
  ],
  "k8s-cluster": {
    "children": [
      "kube-master",
      "kube-node"
    ]
  },
  "kube-master": [
    "ip-172-31-3-xxx.us-east-2.compute.internal"
  ],
  "kube-node": [
    "ip-172-31-8-xxx.us-east-2.compute.internal"
  ]
}
```

Guide:

- Create instances in AWS as needed.
- Either during or after creation, add tags to the instances with a key of `kubespray-role` and a value of `kube-master`, `etcd`, or `kube-node`. You can also share roles like `kube-master, etcd`
- Copy the `kubespray-aws-inventory.py` script from `kubespray/contrib/aws_inventory` to the `kubespray/inventory` directory.
- Set the following AWS credentials and info as environment variables in your terminal:

```ShellSession
export AWS_ACCESS_KEY_ID="xxxxx"
export AWS_SECRET_ACCESS_KEY="yyyyy"
export REGION="us-east-2"
```

- We will now create our cluster. There will be either one or two small changes. The first is that we will specify `-i inventory/kubespray-aws-inventory.py` as our inventory script. The other is conditional. If your AWS instances are public facing, you can set the `VPC_VISIBILITY` variable to `public` and that will result in public IP and DNS names being passed into the inventory. This causes your cluster.yml command to look like `VPC_VISIBILITY="public" ansible-playbook ... cluster.yml`

## Kubespray configuration

Declare the cloud config variables for the `aws` provider as follows. Setting these variables are optional and depend on your use case.

Variable|Type|Comment
---|---|---
aws_zone|string|Force set the AWS zone. Recommended to leave blank.
aws_vpc|string|The AWS VPC flag enables the possibility to run the master components on a different aws account, on a different cloud provider or on-premise. If the flag is set also the KubernetesClusterTag must be provided
aws_subnet_id|string|SubnetID enables using a specific subnet to use for ELB's
aws_route_table_id|string|RouteTableID enables using a specific RouteTable
aws_role_arn|string|RoleARN is the IAM role to assume when interaction with AWS APIs
aws_kubernetes_cluster_tag|string|KubernetesClusterTag is the legacy cluster id we'll use to identify our cluster resources
aws_kubernetes_cluster_id|string|KubernetesClusterID is the cluster id we'll use to identify our cluster resources
aws_disable_security_group_ingress|bool|The aws provider creates an inbound rule per load balancer on the node security group. However, this can run into the AWS security group rule limit of 50 if many LoadBalancers are created. This flag disables the automatic ingress creation. It requires that the user has setup a rule that allows inbound traffic on kubelet ports from the local VPC subnet (so load balancers can access it). E.g. 10.82.0.0/16 30000-32000.
aws_elb_security_group|string|Only in Kubelet version >= 1.7 : AWS has a hard limit of 500 security groups. For large clusters creating a security group for each ELB can cause the max number of security groups to be reached. If this is set instead of creating a new Security group for each ELB this security group will be used instead.
aws_disable_strict_zone_check|bool|During the instantiation of an new AWS cloud provider, the detected region is validated against a known set of regions. In a non-standard, AWS like environment (e.g. Eucalyptus), this check may be undesirable.  Setting this to true will disable the check and provide a warning that the check was skipped.  Please note that this is an experimental feature and work-in-progress for the moment.
