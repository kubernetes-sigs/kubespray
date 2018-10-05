Local Storage Provisioner
=========================

The local storage provisioner is NOT a dynamic storage provisioner as you would
expect from a cloud provider. Instead, it simply creates PersistentVolumes for
all manually created volumes located in the directories specified in the `local_volume_provisioner_storage_classes.host_dir` entries.
The default path is /mnt/disks and the rest of this doc will use that path as
an example.

Examples to create local storage volumes
----------------------------------------

### tmpfs method:

``` bash
for vol in vol1 vol2 vol3; do
mkdir /mnt/disks/$vol
mount -t tmpfs -o size=5G $vol /mnt/disks/$vol
done
```

The tmpfs method is not recommended for production because the mount is not
persistent and data will be deleted on reboot.

### Mount physical disks

``` bash
mkdir /mnt/disks/ssd1
mount /dev/vdb1 /mnt/disks/ssd1
```

Physical disks are recommended for production environments because it offers
complete isolation in terms of I/O and capacity.

### File-backed sparsefile method

``` bash
truncate /mnt/disks/disk5 --size 2G
mkfs.ext4 /mnt/disks/disk5
mkdir /mnt/disks/vol5
mount /mnt/disks/disk5 /mnt/disks/vol5
```

If you have a development environment and only one disk, this is the best way
to limit the quota of persistent volumes.

### Simple directories

In a development environment using `mount --bind` works also, but there is no capacity
management.

### Block volumeMode PVs

Create a symbolic link under discovery directory to the block device on the node. To use
raw block devices in pods BlockVolume feature gate must be enabled.

Usage notes
-----------

Beta PV.NodeAffinity field is used by default. If running against an older K8s
version, the useAlphaAPI flag must be set in the configMap.

The volume provisioner cannot calculate volume sizes correctly, so you should
delete the daemonset pod on the relevant host after creating volumes. The pod
will be recreated and read the size correctly.

Make sure to make any mounts persist via /etc/fstab or with systemd mounts (for
CoreOS/Container Linux). Pods with persistent volume claims will not be
able to start if the mounts become unavailable.

Further reading
---------------

Refer to the upstream docs here: <https://github.com/kubernetes-incubator/external-storage/tree/master/local-volume>
