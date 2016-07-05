Vagrant Install
=================

Assuming you have Vagrant (1.8+) installed with virtualbox (it may work
with vmware, but is untested) you should be able to launch a 3 node
Kubernetes cluster by simply running `$ vagrant up`.<br />

This will spin up 3 VMs and install kubernetes on them.  Once they are
completed you can connect to any of them by running <br />
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
