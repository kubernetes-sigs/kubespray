# Deploy CoreDNS External into Kubespray/Kubernetes
```
Makes use of the CoreDNS plugin "k8s_external" to allow an additional zone to resolve external IP addresses
```

[k8s_external](https://coredns.io/plugins/k8s_external/)

## Install
```
Defaults can be found in contrib/external-coredns/roles/provision/defaults/main.yml. You can override the defaults by copying the contents of this file to somewhere in inventory/mycluster/group_vars such as inventory/mycluster/groups_vars/k8s-cluster/addons.yml and making any adjustments as required.

ansible-playbook --ask-become -i inventory/sample/hosts.ini contrib/external-coredns/external-coredns.yml
```
