Local Storage Provisioner
=========================

The [local storage provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/local-volume)
is NOT a dynamic storage provisioner as you would
expect from a cloud provider. Instead, it simply creates PersistentVolumes for
all mounts under the host_dir of the specified storage class.
These storage classes are specified in the `local_volume_provisioner_storage_classes` nested dictionary.
Example:

```yaml
local_volume_provisioner_storage_classes:
  local-storage:
    host_dir: /mnt/disks
    mount_dir: /mnt/disks
  fast-disks:
    host_dir: /mnt/fast-disks
    mount_dir: /mnt/fast-disks
    block_cleaner_command:
       - "/scripts/shred.sh"
       - "2"
    volume_mode: Filesystem
    fs_type: ext4
```

For each key in `local_volume_provisioner_storage_classes` a storageClass with the
same name is created. The subkeys of each storage class are converted to camelCase and added
as attributes to the storageClass.
The result of the above example is:

```yaml
data:
  storageClassMap: |
    local-storage:
      hostDir: /mnt/disks
      mountDir: /mnt/disks
    fast-disks:
      hostDir: /mnt/fast-disks
      mountDir:  /mnt/fast-disks
      blockCleanerCommand:
        - "/scripts/shred.sh"
        - "2"
      volumeMode: Filesystem
      fsType: ext4
```

The default StorageClass is local-storage on /mnt/disks,
the rest of this doc will use that path as an example.

Examples to create local storage volumes
----------------------------------------

1. tmpfs method:

``` bash
for vol in vol1 vol2 vol3; do
mkdir /mnt/disks/$vol
mount -t tmpfs -o size=5G $vol /mnt/disks/$vol
done
```

The tmpfs method is not recommended for production because the mount is not
persistent and data will be deleted on reboot.

1. Mount physical disks

``` bash
mkdir /mnt/disks/ssd1
mount /dev/vdb1 /mnt/disks/ssd1
```

Physical disks are recommended for production environments because it offers
complete isolation in terms of I/O and capacity.

1. Mount unpartitioned physical devices

``` bash
for disk in /dev/sdc /dev/sdd /dev/sde; do
  ln -s $disk /mnt/disks
done
```

This saves time of precreatnig filesystems. Note that your storageclass must have
volume_mode set to "Filesystem" and fs_type defined. If either is not set, the
disk will be added as a raw block device.

1. File-backed sparsefile method

``` bash
truncate /mnt/disks/disk5 --size 2G
mkfs.ext4 /mnt/disks/disk5
mkdir /mnt/disks/vol5
mount /mnt/disks/disk5 /mnt/disks/vol5
```

If you have a development environment and only one disk, this is the best way
to limit the quota of persistent volumes.

1. Simple directories

In a development environment using `mount --bind` works also, but there is no capacity
management.

1. Block volumeMode PVs

Create a symbolic link under discovery directory to the block device on the node. To use
raw block devices in pods, volume_type should be set to "Block".

Usage notes
-----------

Beta PV.NodeAffinity field is used by default. If running against an older K8s
version, the useAlphaAPI flag must be set in the configMap.

The volume provisioner cannot calculate volume sizes correctly, so you should
delete the daemonset pod on the relevant host after creating volumes. The pod
will be recreated and read the size correctly.

Make sure to make any mounts persist via /etc/fstab or with systemd mounts (for
Flatcar Container Linux). Pods with persistent volume claims will not be
able to start if the mounts become unavailable.

Further reading
---------------

Refer to the upstream docs here: <https://github.com/kubernetes-incubator/external-storage/tree/master/local-volume>
