# Deploy MetalLB into Kubespray/Kubernetes
```
MetalLB hooks into your Kubernetes cluster, and provides a network load-balancer implementation. In short, it allows you to create Kubernetes services of type “LoadBalancer” in clusters that don’t run on a cloud provider, and thus cannot simply hook into paid products to provide load-balancers.
```
This playbook aims to automate [this](https://metallb.universe.tf/concepts/layer2/). It deploys MetalLB into kubernetes and sets up a layer 2 loadbalancer.

## Install
```
Defaults can be found in contrib/metallb/roles/provision/defaults/main.yml. You can override the defaults by copying the contents of this file to somewhere in inventory/mycluster/group_vars such as inventory/mycluster/groups_vars/k8s-cluster/addons.yml and making any adjustments as required.

ansible-playbook --ask-become -i inventory/sample/hosts.ini contrib/metallb/metallb.yml
```
