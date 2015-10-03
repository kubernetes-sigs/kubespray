kubernetes-ansible
========

Install and configure a kubernetes cluster including network overlay and optionnal addons.
Based on [CiscoCloud](https://github.com/CiscoCloud/kubernetes-ansible) work.

Requirements
------------
Tested on debian Jessie and Ubuntu.
The target servers must have access to the Internet in order to pull docker imaqes


Ansible
-------------------------
## Variables

## Run ansible playbook
It is possible to define variables for different environments.
For instance, in order to deploy the cluster on 'dev' environment run the following command.
```
ansible-playbook -i environments/dev/inventory cluster.yml
```

Kubernetes
-------------------------
## Check cluster status


Known issues
-------------
## Node reboot and Calico

## Monitoring addon

## Etcd failover

Author Information
------------------

Smana - Smaine Kahlouch (smaine.kahlouch@gmail.com)
