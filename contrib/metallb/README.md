# Deploy MetalLB into Kubespray/Kubernetes
```
MetalLB hooks into your Kubernetes cluster, and provides a network load-balancer implementation. In short, it allows you to create Kubernetes services of type “LoadBalancer” in clusters that don’t run on a cloud provider, and thus cannot simply hook into paid products to provide load-balancers.
```
This playbook aims to automate [this](https://metallb.universe.tf/tutorial/layer2/tutorial). It deploys MetalLB into kubernetes and sets up a layer 2 loadbalancer.

## Install
```
ansible-playbook --ask-become -i inventory/sample/k8s_heketi_inventory.yml contrib/metallb/metallb.yml
```
