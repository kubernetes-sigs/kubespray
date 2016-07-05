Cloud providers
==============

#### Provisioning

You can use kargo-cli to start new instances on cloud providers
here's an example
```
kargo [aws|gce] --nodes 2 --etcd 3 --cluster-name test-smana
```

#### Deploy kubernetes

With kargo-cli
```
kargo deploy [--aws|--gce] -u admin
```

Or ansible-playbook command
```
ansible-playbook -u smana -e ansible_ssh_user=admin -e cloud_provider=[aws|gce] -b --become-user=root -i inventory/single.cfg cluster.yml
```
