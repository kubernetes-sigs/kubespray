vagrant-k8s
===========
Scripts to create libvirt lab with vagrant and prepare some stuff for `k8s` deployment with `kargo`.


Requirements
============

* vagrant
* vagrant-libvirt plugin

How-to
======

* Prepare the virtual lab:

```bash
export VAGRANT_POOL="10.100.0.0/16"
git clone https://github.com/adidenko/vagrant-k8s
cd vagrant-k8s
vagrant up
```

* Login to master node and deploy k8s with kargo:

```bash
vagrant ssh $USER-k8s-01
# Inside your master VM run this:
sudo su -
./deploy-k8s.kargo.sh
```
