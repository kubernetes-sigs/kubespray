# Deploy Heketi/Glusterfs into Kubespray/Kubernetes
This playbook aims to automate [this](https://github.com/heketi/heketi/blob/master/docs/admin/install-kubernetes.md) tutorial. It deploys heketi/glusterfs into kubernetes and sets up a storageclass.

## Client Setup
Heketi provides a CLI that provides users with a means to administer the deployment and configuration of GlusterFS in Kubernetes. [Download and install the heketi-cli](https://github.com/heketi/heketi/releases) on your client machine.

## Install
Copy the inventory.yml.sample over to inventory/sample/k8s_heketi_inventory.yml and change it according to your setup.
```
ansible-playbook --ask-become -i inventory/sample/k8s_heketi_inventory.yml contrib/network-storage/heketi/heketi.yml
```

## Tear down
```
ansible-playbook --ask-become -i inventory/sample/k8s_heketi_inventory.yml contrib/network-storage/heketi/heketi-tear-down.yml
```

Add `--extra-vars "heketi_remove_lvm=true"` to the command above to remove LVM packages from the system
