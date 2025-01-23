This will install `nfs-common` on Debian based systems, and `nfs-utils` on RedHat based systems to all hosts with the role `kube_node` in the inventory file.

```
ansible-playbook -b --become-user=root -i inventory/sample/inventory.ini --user=ubuntu ./contrib/network-storage/nfs/nfs-client.yml
```
