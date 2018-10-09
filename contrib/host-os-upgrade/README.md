# Host OS upgrade

Use this playbook to upgrade hosts, invoke using the same command that you used for `cluster.yml`.

This playbook leverages the main `upgrade/pre-upgrade`and `upgrade/post-upgrade` playbooks, preseeding `drain_nodes` to true.

## Things to be aware of

### Cluster overload

During the update process, there will be reduced availability of compute resources, please be aware of your cluster capacity.

After the update, any stateful service relying on replication between hosts might need to resyncronize either automatically or manually(if it lost its quorum), be aware that during any syncronization work, the service's performance will be degraded and network traffic will be increased.

### Etcd quorum loss

Ensure to set a serial low enough to allow all of your servers to be taken offline while still keeping Kubernetes data store functional or the cluster might lose its sync.

For more info on this topic, check out the [upstream Kubernetes guide on managing etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)

### Pod reschedule

The pods will be rescheduled, make sure your applications and services can tolerate a node drain without too much disruption.
During the update, some evictions may occour, please use `PodDisruptionBudget` and `PodPriorityClass` to enforce rules about critical services.

### Playbook execution failure

If the playbook execution fails before the uncordoning is performed, the node might be healthy but excluded from the cluster, you can verify if you are experiencing this situation by issuing

```bash
$ kubectl get nodes

NAME      STATUS                     AGE       VERSION
cordoned  Ready,SchedulingDisabled   11h       v1.12.1
node1     Ready                      11h       v1.12.1
node2     Ready                      11h       v1.12.1
node3     Ready                      11h       v1.12.1
node4     Ready                      11h       v1.12.1
```

In this example, `cordoned` is ready but unavailable by the cluster.

If the node is cordoned, uncordon it by issuing a `kubectl uncordon <NODENAME>`

### Swap

After a reboot, the nodes might have their swap reactivated, disable it by issuing `swapoff -a

## Upgrade sequence

These actions will be performed on 10% of nodes at a time, this can be configured by setting the `serial` variable

* Cordon and drain node
* Refresh package cache and upgrade packages
* Reboot system
* Uncordon node

## Supported OS list

In general this playbook leverages Ansible's `apt`,`dnf` and `yum` modules so it should work properly on any system using these package managers

* Centos 7
* Debian Buster
* Debian Stretch
* Fedora 28
* Ubuntu Bionic Beaver (18.04)

## Future work

### Debian / Ubuntu

* Use /var/run/reboot-required to check if a reboot is really needed

### Centos

* Parse output from `needs-restarting` to restart services and eventually the system

### Fedora

* Use dnf plugin to check if any service needs to restart
