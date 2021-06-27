# Fedora CoreOS

Tested with stable version 31.20200223.3.0.

Because package installation with `rpm-ostree` requires a reboot, playbook may fail while bootstrap.
Restart playbook again.

## Containers

Tested with

- docker
- crio

### docker

OS base packages contains docker.

### cri-o

To use `cri-o` disable docker service with ignition:

```yaml
#workaround, see https://github.com/coreos/fedora-coreos-tracker/issues/229
systemd:
  units:
    - name: docker.service
      enabled: false
      contents: |
        [Unit]
        Description=disable docker

        [Service]

        [Install]
        WantedBy=multi-user.target
```

## Network

### calico

To use calico create sysctl file with ignition:

```yaml
files:
    - path: /etc/sysctl.d/reverse-path-filter.conf
      contents:
        inline: |
          net.ipv4.conf.all.rp_filter=1
```

## libvirt setup

### Prepare

Prepare ignition and serve via http (a.e. python -m http.server )

```json
{
  "ignition": {
     "version": "3.0.0"
  },

  "passwd": {
    "users": [
      {
        "name": "ansibleUser",
        "sshAuthorizedKeys": [
          "ssh-rsa ..publickey.."
        ],
        "groups": [ "wheel" ]
      }
    ]
  }
}
```

### create guest

```shell script
fcos_version=31.20200223.3.0
kernel=https://builds.coreos.fedoraproject.org/prod/streams/stable/builds/${fcos_version}/x86_64/fedora-coreos-${fcos_version}-live-kernel-x86_64
initrd=https://builds.coreos.fedoraproject.org/prod/streams/stable/builds/${fcos_version}/x86_64/fedora-coreos-${fcos_version}-live-initramfs.x86_64.img
ignition_url=http://mywebserver/fcos.ign
kernel_args="ip=dhcp rd.neednet=1 console=tty0 coreos.liveiso=/ console=ttyS0 coreos.inst.install_dev=/dev/sda coreos.inst.stream=stable coreos.inst.ignition_url=${ignition_url}"
sudo virt-install --name ${machine_name} --ram 4048 --graphics=none --vcpus 2 --disk size=20 \
                --network bridge=virbr0 \
                --install kernel=${kernel},initrd=${initrd},kernel_args_overwrite=yes,kernel_args="${kernel_args}"
```
