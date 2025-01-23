# Install "nfs-client" software onto hosts with the `kube_node` role
By running the following command `nfs-common` on Debian based systems, and `nfs-utils` on RedHat based systems will be installed to all hosts with the role `kube_node` in your inventory file.

```shell
ansible-playbook -b --become-user=root -i inventory/sample/inventory.ini --user=ubuntu ./contrib/network-storage/nfs/nfs-client.yml
```
