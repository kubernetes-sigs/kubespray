vagrant-k8s
===========
Scripts to create libvirt lab with vagrant and prepare some stuff for `k8s` deployment with `kargo`.


Requirements
============

* `libvirt`
* `vagrant`
* `vagrant-libvirt` plugin (`vagrant plugin install vagrant-libvirt`)
* `$USER` should be able to connect to libvirt (test with `virsh list --all`)

How-to
======

* Change default IP pool for vagrant networks if you want:

```bash
export VAGRANT_POOL="10.100.0.0/16"
```

* Prepare the virtual lab:

```bash
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
