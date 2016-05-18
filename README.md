

![Kubespray Logo](http://s9.postimg.org/md5dyjl67/kubespray_logoandkubespray_small.png)

# Deploy a production ready kubernetes cluster

- Can be deployed on **AWS, GCE, OpenStack or Baremetal**
- **High available** cluster
- **Composable** (Choice of the network plugin for instance)
- Support most popular **Linux distributions**
- **Continuous integration tests**

# Getting Started

To deploy the cluster you can use :

## kargo-cli

[**kargo-cli**](https://github.com/kubespray/kargo-cli)
 
## Vagrant

Assuming you have Vagrant (1.8+) installed with virtualbox (it may work
with vmware, but is untested) you should be able to launch a 3 node 
Kubernetes cluster by simply running `$ vagrant up`.

This will spin up 3 VMs and install kubernetes on them.  Once they are 
completed you can connect to any of them by running 
`$ vagrant ssh k8s-0[1..3]`.

```
$ vagrant up
Bringing machine 'k8s-01' up with 'virtualbox' provider...
Bringing machine 'k8s-02' up with 'virtualbox' provider...
Bringing machine 'k8s-03' up with 'virtualbox' provider...
==> k8s-01: Box 'bento/ubuntu-14.04' could not be found. Attempting to find and install...
...
...
    k8s-03: Running ansible-playbook...

PLAY [k8s-cluster] *************************************************************

TASK [setup] *******************************************************************
ok: [k8s-03]
ok: [k8s-01]
ok: [k8s-02]
...
...
PLAY RECAP *********************************************************************
k8s-01                     : ok=157  changed=66   unreachable=0    failed=0   
k8s-02                     : ok=137  changed=59   unreachable=0    failed=0   
k8s-03                     : ok=86   changed=51   unreachable=0    failed=0   

$ vagrant ssh k8s-01
vagrant@k8s-01:~$ kubectl get nodes
NAME      STATUS    AGE
k8s-01    Ready     45s
k8s-02    Ready     45s
k8s-03    Ready     45s
```


## Ansible

**Ansible** usual commands

# Further Reading

A complete **documentation** can be found [**here**](https://docs.kubespray.io)

if you have any question you can **chat** with us  [![SlackStatus](https://slack.kubespray.io/badge.svg)](https://kubespray.slack.com)

[![Build Status](https://travis-ci.org/kubespray/kargo.svg)](https://travis-ci.org/kubespray/kargo) </br>
CI tests sponsored by Google (GCE), and [teuto.net](https://teuto.net/) for OpenStack.
