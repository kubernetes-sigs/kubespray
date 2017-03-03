AWS
===============

To deploy kubespray on [AWS](https://aws.amazon.com/) uncomment the `cloud_provider` option in `group_vars/all.yml` and set it to `'aws'`.

Prior to creating your instances, you **must** ensure that you have created IAM roles and policies for both "kubernetes-master" and "kubernetes-node". You can find the IAM policies [here](https://github.com/kubernetes-incubator/kargo/tree/master/contrib/aws_iam/). See the [IAM Documentation](https://aws.amazon.com/documentation/iam/) if guidance is needed on how to set these up. When you bring your instances online, associate them with the respective IAM role. Nodes that are only to be used for Etcd do not need a role.

The next step is to make sure the hostnames in your `inventory` file are identical to your internal hostnames in AWS. This may look something like `ip-111-222-333-444.us-west-2.compute.internal`. You can then specify how Ansible connects to these instances with `ansible_ssh_host` and `ansible_ssh_user`.

You can now create your cluster!
