# Cloud providers

## Provisioning

You can deploy instances in your cloud environment in several ways. Examples include Terraform, Ansible (ec2 and gce modules), and manual creation.

## Deploy kubernetes

With ansible-playbook command

```ShellSession
ansible-playbook -u smana -e ansible_ssh_user=admin -e cloud_provider=[aws|gce] -b --become-user=root -i inventory/single.cfg cluster.yml
```
