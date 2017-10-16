Vagrant Install
=================

Assuming you have Vagrant (1.9+) installed with virtualbox (it may work
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

Customize Vagrant
=================

You can override the default settings in the `Vagrantfile` either by directly modifying the `Vagrantfile`
or through an override file.

In the same directory as the `Vagrantfile`, create a folder called `vagrant` and create `config.rb` file in it.

You're able to override the variables defined in `Vagrantfile` by providing the value in the `vagrant/config.rb` file,
e.g.:

    echo '$forwarded_ports = {8001 => 8001}' >> vagrant/config.rb

and after `vagrant up` or `vagrant reload`, your host will have port forwarding setup with the guest on port 8001.

Use alternative OS for Vagrant
==============================

By default, Vagrant uses Ubuntu 16.04 box to provision a local cluster. You may use an alternative supported
operating system for your local cluster.

Customize `$os` variable in `Vagrantfile` or as override, e.g.,:

    echo '$os = "coreos-stable"' >> vagrant/config.rb


The supported operating systems for vagrant are defined in the `SUPPORTED_OS` constant in the `Vagrantfile`.
