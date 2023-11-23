# Fedora CoreOS

Tested with stable version 37.20230322.3.0

Because package installation with `rpm-ostree` requires a reboot, playbook may fail while bootstrap.
Restart playbook again.

## Containers

Tested with

- containerd
- crio

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

```ShellSeasion
machine_name=myfcos1
ignition_url=http://mywebserver/fcos.ign

fcos_version=34.20210611.3.0
kernel=https://builds.coreos.fedoraproject.org/prod/streams/stable/builds/${fcos_version}/x86_64/fedora-coreos-${fcos_version}-live-kernel-x86_64
initrd=https://builds.coreos.fedoraproject.org/prod/streams/stable/builds/${fcos_version}/x86_64/fedora-coreos-${fcos_version}-live-initramfs.x86_64.img
rootfs=https://builds.coreos.fedoraproject.org/prod/streams/stable/builds/${fcos_version}/x86_64/fedora-coreos-${fcos_version}-live-rootfs.x86_64.img
kernel_args="console=ttyS0 coreos.live.rootfs_url=${rootfs} coreos.inst.install_dev=/dev/sda coreos.inst.stream=stable coreos.inst.ignition_url=${ignition_url}"
sudo virt-install --name ${machine_name} --ram 4048 --graphics=none --vcpus 2 --disk size=20 \
                --network bridge=virbr0 \
                --install kernel=${kernel},initrd=${initrd},kernel_args_overwrite=yes,kernel_args="${kernel_args}"
```

## Downloading files with kubespray
Occurred somewhere between FCOS 37 and 39- wget needs to be manually added with ignition to download files (container runtime, etc.)

```
systemd:
  units:
    - name: kubespray-support.service
      enabled: true
      contents: |
        [Unit]
        Description=Layer packages with rpm-ostree
        # We run after `systemd-machine-id-commit.service` to ensure that
        # `ConditionFirstBoot=true` services won't rerun on the next boot.
        After=systemd-machine-id-commit.service
        After=network-online.target
        # We run before `zincati.service` to avoid conflicting rpm-ostree
        # transactions.
        Before=zincati.service
        ConditionPathExists=!/var/lib/kubespray-support.stamp

        [Service]
        Type=oneshot
        RemainAfterExit=yes
        ExecStart=/usr/bin/rpm-ostree install --allow-inactive python3 libselinux-python3 wget --reboot
        ExecStart=/bin/touch /var/lib/kubespray-support.stamp
        ExecStart=/bin/systemctl --no-block reboot```
