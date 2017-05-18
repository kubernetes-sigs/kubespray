AWS
===============

To deploy kubespray on [AWS](https://aws.amazon.com/) uncomment the `cloud_provider` option in `group_vars/all.yml` and set it to `'aws'`.

Prior to creating your instances, you **must** ensure that you have created IAM roles and policies for both "kubernetes-master" and "kubernetes-node". You can find the IAM policies [here](https://github.com/kubernetes-incubator/kargo/tree/master/contrib/aws_iam/). See the [IAM Documentation](https://aws.amazon.com/documentation/iam/) if guidance is needed on how to set these up. When you bring your instances online, associate them with the respective IAM role. Nodes that are only to be used for Etcd do not need a role.

The next step is to make sure the hostnames in your `inventory` file are identical to your internal hostnames in AWS. This may look something like `ip-111-222-333-444.us-west-2.compute.internal`. You can then specify how Ansible connects to these instances with `ansible_ssh_host` and `ansible_ssh_user`.

You can now create your cluster!

### Dynamic Inventory ###
There is also a dynamic inventory script for AWS that can be used if desired. However, be aware that it makes some certain assumptions about how you'll create your inventory. It also does not handle all use cases and groups that we may use as part of more advanced deployments. Additions welcome.

This will produce an inventory that is passed into Ansible that looks like the following:
```
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
- Either during or after creation, add tags to the instances with a key of `kargo-role` and a value of `kube-master`, `etcd`, or `kube-node`. You can also share roles like `kube-master, etcd`
- Copy the `kargo-aws-inventory.py` script from `kargo/contrib/aws_inventory` to the `kargo/inventory` directory.
- Set the following AWS credentials and info as environment variables in your terminal:
```
export AWS_ACCESS_KEY_ID="xxxxx"
export AWS_SECRET_ACCESS_KEY="yyyyy"
export REGION="us-east-2"
```
- We will now create our cluster. There will be either one or two small changes. The first is that we will specify `-i inventory/kargo-aws-inventory.py` as our inventory script. The other is conditional. If your AWS instances are public facing, you can set the `VPC_VISIBILITY` variable to `public` and that will result in public IP and DNS names being passed into the inventory. This causes your cluster.yml command to look like `VPC_VISIBILITY="public" ansible-playbook ... cluster.yml`
