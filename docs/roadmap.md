# Kubespray's roadmap

## Self deployment (pull-mode) [#320](https://github.com/kubespray/kubespray/issues/320)

- the playbook would install and configure docker and the etcd cluster
- the following data would be inserted into etcd: certs,tokens,users,inventory,group_vars.
- a "kubespray" container would be deployed (kubespray-cli, ansible-playbook)
- to be discussed, a way to provide the inventory
- **self deployment** of the node from inside a container [#321](https://github.com/kubespray/kubespray/issues/321)

## Provisioning and cloud providers

- [ ] Terraform to provision instances on:
  - [ ] GCE
  - [x] AWS (contrib/terraform/aws)
  - [x] Openstack (contrib/terraform/openstack)
  - [x] Packet
  - [ ] Digital Ocean
  - [ ] Azure
- [ ] On AWS autoscaling, multi AZ
- [ ] On Azure autoscaling, create loadbalancer [#297](https://github.com/kubespray/kubespray/issues/297)
- [ ] On GCE be able to create a loadbalancer automatically (IAM ?) [#280](https://github.com/kubespray/kubespray/issues/280)
- [x] **TLS bootstrap** support for kubelet (covered by kubeadm, but not in standard deployment) [#234](https://github.com/kubespray/kubespray/issues/234)
  (related issues: <https://github.com/kubernetes/kubernetes/pull/20439> <https://github.com/kubernetes/kubernetes/issues/18112)>

## Tests

- [x] Run kubernetes e2e tests
- [ ] Test idempotency on single OS but for all network plugins/container engines
- [ ] single test on AWS per day
- [ ] test scale up cluster:  +1 etcd, +1 master, +1 node
- [x] Reorganize CI test vars into group var files

## Lifecycle

- [ ] Upgrade granularity: select components to upgrade and skip others

## Networking

- [ ] Opencontrail
- [ ] Consolidate roles/network_plugin and roles/kubernetes-apps/network_plugin

## Kubespray API

- Perform all actions through an **API**
- Store inventories / configurations of multiple clusters
- Make sure that state of cluster is completely saved in no more than one config file beyond hosts inventory

## Addons (helm or native ansible)

- [x] Helm
- [x] Ingress-nginx
- [x] kubernetes-dashboard

## Others

- Organize and update documentation (split in categories)
- Refactor downloads so it all runs in the beginning of deployment
- Make bootstrapping OS more consistent
- **consul** -> if officially supported by k8s
- Flex volumes options (e.g. **torrus** support) [#312](https://github.com/kubespray/kubespray/issues/312)
- Clusters federation option (aka **ubernetes**) [#329](https://github.com/kubespray/kubespray/issues/329)
