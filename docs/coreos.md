CoreOS bootstrap
===============

Example with **kargo-cli**:

```
kargo deploy --gce --coreos
```

Or with Ansible:

Before running the cluster playbook you must satisfy the following requirements:

* On each CoreOS nodes a writable directory **/opt/bin** (~400M disk space)

* Uncomment the variable **ansible\_python\_interpreter** in the file `inventory/group_vars/all.yml`

* run the Python bootstrap playbook

```
ansible-playbook -u smana -e ansible_ssh_user=smana  -b --become-user=root -i inventory/inventory.cfg coreos-bootstrap.yml
```

Then you can proceed to [cluster deployment](#run-deployment)
