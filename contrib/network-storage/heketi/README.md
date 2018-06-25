# Deploy Heketi/Glusterfs into Kubespray/Kubernetes
This playbook aims to automate (this)[https://github.com/heketi/heketi/blob/master/docs/admin/install-kubernetes.md] tutorial. It deploys heketi/glusterfs into kubernetes and sets up a storageclass.

## Install
Copy the inventory.yml.sample over to inventory/sample/k8s_heketi_inventory.yml and change it according to your setup.
```
ansible-playbook -b --ask-become -i inventory/sample/k8s_heketi_inventory.yml contrib/network-storage/heketi/heketi.yml
```
