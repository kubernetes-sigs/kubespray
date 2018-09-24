# Install the packet CI cluster

## Deploy kubernetes

The CI jobs are kubernetes-pods, the first steps is to deploy kubernetes on the CI nodes.

1. Edit/update the inventory`kubespray-packet/hosts.ini`
2. Review configuration in the groups_vars `kubespray-packet/group_vars/*`
3. Deploy/upgrade the cluster:

``` bash
$ make deploy
ansible-playbook -i kubespray-packet/hosts.ini -vv ../cluster.yml -e ansible_ssh_user=root
```

## Package the VM images inside containers

The role `kubevirt-images`, will download all the base vm-images defined in `create-images/vars.yml` and push them the quay.io/kubespray docker registry

```
$ cd create-images && make deploy
```
