# Atomic host bootstrap

Atomic host testing has been done with the network plugin flannel. Change the inventory var `kube_network_plugin: flannel`.

Note: Flannel is the only plugin that has currently been tested with atomic

## Vagrant

* For bootstrapping with Vagrant, use box centos/atomic-host or fedora/atomic-host
* Update VagrantFile variable `local_release_dir` to `/var/vagrant/temp`.
* Update `vm_memory = 2048` and `vm_cpus = 2`
* Networking on vagrant hosts has to be brought up manually once they are booted.

    ```ShellSession
    vagrant ssh
    sudo /sbin/ifup enp0s8
    ```

* For users of vagrant-libvirt download centos/atomic-host qcow2 format from <https://wiki.centos.org/SpecialInterestGroup/Atomic/Download/>
* For users of vagrant-libvirt download fedora/atomic-host qcow2 format from <https://dl.fedoraproject.org/pub/alt/atomic/stable/>

Then you can proceed to [cluster deployment](#run-deployment)
