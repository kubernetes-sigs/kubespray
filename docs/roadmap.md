Kargo's roadmap
=================

### Kubeadm
- Propose kubeadm as an option in order to setup the kubernetes cluster.
That would probably improve deployment speed and certs management [#553](https://github.com/kubespray/kargo/issues/553)

### Self deployment (pull-mode) [#320](https://github.com/kubespray/kargo/issues/320)
- the playbook would install and configure docker/rkt and the etcd cluster
- the following data would be inserted into etcd: certs,tokens,users,inventory,group_vars.
- a "kubespray" container would be deployed (kargo-cli, ansible-playbook, kpm)
- to be discussed, a way to provide the inventory
- **self deployment** of the node from inside a container [#321](https://github.com/kubespray/kargo/issues/321)

### Provisionning and cloud providers
- [ ] Terraform to provision instances on **GCE, AWS, Openstack, Digital Ocean, Azure**
- [ ] On AWS autoscaling, multi AZ
- [ ] On Azure autoscaling, create loadbalancer [#297](https://github.com/kubespray/kargo/issues/297)
- [ ] On GCE be able to create a loadbalancer automatically (IAM ?) [#280](https://github.com/kubespray/kargo/issues/280)
- [x] **TLS boostrap** support for kubelet [#234](https://github.com/kubespray/kargo/issues/234)
  (related issues: https://github.com/kubernetes/kubernetes/pull/20439 <br>
   https://github.com/kubernetes/kubernetes/issues/18112)

### Tests
- [x] Run kubernetes e2e tests
- [x] migrate to jenkins
(a test is currently a deployment on a 3 node cluste, testing k8s api, ping between 2 pods)
- [x] Full tests on GCE per day (All OS's, all network plugins)
- [x] trigger a single test per pull request
- [ ] ~~single test with the Ansible version n-1 per day~~
- [x] Test idempotency on on single OS but for all network plugins/container engines
- [ ] single test on AWS per day
- [x] test different achitectures :
           - 3 instances, 3 are members of the etcd cluster, 2 of them acting as master and node, 1 as node
           - 5 instances, 3 are etcd and nodes, 2 are masters only
           - 7 instances, 3 etcd only, 2 masters, 2 nodes
- [ ] test scale up cluster:  +1 etcd, +1 master, +1 node

### Lifecycle
- [ ] Adopt the kubeadm tool by delegating CM tasks it is capable to accomplish well [#553](https://github.com/kubespray/kargo/issues/553)
- [x] Drain worker node when upgrading k8s components in a worker node. [#154](https://github.com/kubespray/kargo/issues/154)
- [ ] Drain worker node when shutting down/deleting an instance
- [ ] Upgrade granularity: select components to upgrade and skip others

### Networking
- [ ] romana.io support [#160](https://github.com/kubespray/kargo/issues/160)
- [ ] Configure network policy for Calico. [#159](https://github.com/kubespray/kargo/issues/159)
- [ ] Opencontrail
- [x] Canal
- [x] Cloud Provider native networking (instead of our network plugins)

### High availability
- (to be discussed) option to set a loadbalancer for the apiservers like ucarp/packemaker/keepalived
While waiting for the issue [kubernetes/kubernetes#18174](https://github.com/kubernetes/kubernetes/issues/18174) to be fixed.

### Kargo-cli
- Delete instances
- `kargo vagrant` to setup a test cluster locally
- `kargo azure` for Microsoft Azure support
- switch to Terraform instead of Ansible for provisionning
- update $HOME/.kube/config when a cluster is deployed. Optionally switch to this context

### Kargo API
- Perform all actions through an **API**
- Store inventories / configurations of mulltiple clusters
- make sure that state of cluster is completely saved in no more than one config file beyond hosts inventory

### Addons (with kpm)
Include optionals deployments to init the cluster:
##### Monitoring
- Heapster / Grafana ....
- **Prometheus**

##### Others

##### Dashboards:
 - kubernetes-dashboard
 - Fabric8
 - Tectonic
 - Cockpit

##### Paas like
 - Openshift Origin
 - Openstack
 - Deis Workflow

### Others
- remove nodes  (adding is already supported)
- being able to choose any k8s version (almost done)
- **rkt** support [#59](https://github.com/kubespray/kargo/issues/59)
- Review documentation (split in categories)
- **consul** -> if officialy supported by k8s
- flex volumes options (e.g. **torrus** support) [#312](https://github.com/kubespray/kargo/issues/312)
- Clusters federation option (aka **ubernetes**) [#329](https://github.com/kubespray/kargo/issues/329)
