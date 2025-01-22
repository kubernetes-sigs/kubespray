Install `nfs-common` to all hosts with the role `kube_node`

```
ansible-playbook -b --become-user=root -i inventory/sample/inventory.ini --user=ubuntu ./contrib/network-storage/nfs/nfs-common.yml
```