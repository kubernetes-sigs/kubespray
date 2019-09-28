# Vagrant

## Introduction

[Vagrant](https://www.vagrantup.com) allows you to spin up local testing clusters in order to test Kubespray.

This can be useful to spin up local development clusters or to iterate on the development of Kubespray.

## Prerequisites

- Vagrant > 2.0
- A powerful computer (~2 GB of RAM for each node you want to virtualize)
- `vagrant-libvirt` if you want to add extra disks to nodes

## Quickstart

Create a Python virtualenv

```sh
python -m virtualenv /tmp/venv
```

Activate the Python virtualenv and download required dependencies

```sh
. /tmp/venv/bin/activate
pip install -r requirements.txt
```

Boot up the virtual machines

```sh
vagrant up --no-provision
```

Invoke Kubespray using Vagrant

```sh
vagrant provision
```

___Go grab a coffee___ (Kubespray might take several minutes)

Download the kubeconfig

```sh
vagrant ssh k8s-master-1 -- sudo cat /etc/kubernetes/admin.conf > /tmp/KUBECONFIG
export KUBECONFIG=/tmp/KUBECONFIG
```

Enjoy your multi-node cluster

```sh
$ kubectl get node
NAME           STATUS   ROLES    AGE     VERSION
k8s-master-1   Ready    master   10m     v1.15.3
k8s-master-2   Ready    master   7m37s   v1.15.3
k8s-master-3   Ready    master   7m44s   v1.15.3
k8s-worker-1   Ready    <none>   5m50s   v1.15.3
k8s-worker-2   Ready    <none>   5m50s   v1.15.3
```

```sh
$ kubectl -n kube-system get pod
NAME                                       READY   STATUS    RESTARTS   AGE
calico-kube-controllers-869d84d46f-r7x65   1/1     Running   0          5m
calico-node-bftdq                          1/1     Running   0          5m24s
calico-node-h59rg                          1/1     Running   0          5m24s
calico-node-j6fg2                          1/1     Running   0          5m24s
calico-node-sj5dg                          1/1     Running   0          5m25s
calico-node-xfhf7                          1/1     Running   0          5m24s
coredns-74c9d4d795-kdk9r                   1/1     Running   0          3m56s
coredns-74c9d4d795-tqz7b                   1/1     Running   0          4m38s
dns-autoscaler-576b576b74-2dpl9            1/1     Running   0          4m33s
kube-apiserver-k8s-master-1                1/1     Running   0          5m23s
kube-apiserver-k8s-master-2                1/1     Running   0          5m20s
kube-apiserver-k8s-master-3                1/1     Running   0          5m22s
kube-controller-manager-k8s-master-1       1/1     Running   0          5m22s
kube-controller-manager-k8s-master-2       1/1     Running   0          5m21s
kube-controller-manager-k8s-master-3       1/1     Running   0          5m20s
kube-proxy-dkwvx                           1/1     Running   0          5m16s
kube-proxy-lgbx9                           1/1     Running   0          5m20s
kube-proxy-qvlrp                           1/1     Running   0          5m17s
kube-proxy-sjsb7                           1/1     Running   0          5m17s
kube-proxy-w772g                           1/1     Running   0          5m19s
kube-scheduler-k8s-master-1                1/1     Running   0          5m15s
kube-scheduler-k8s-master-2                1/1     Running   0          5m15s
kube-scheduler-k8s-master-3                1/1     Running   0          5m13s
kubernetes-dashboard-7c547b4c64-7q7kj      1/1     Running   0          4m28s
nginx-proxy-k8s-worker-1                   1/1     Running   0          5m13s
nginx-proxy-k8s-worker-2                   1/1     Running   0          5m14s
nodelocaldns-dk6dc                         1/1     Running   0          4m30s
nodelocaldns-dms7t                         1/1     Running   0          4m31s
nodelocaldns-h8282                         1/1     Running   0          4m31s
nodelocaldns-jqk8m                         1/1     Running   0          4m31s
nodelocaldns-pj8lh                         1/1     Running   0          4m30s
```

## How-tos

### Setting a variable

Open `Vagrantfile` and edit the `EXTRA_VARS` as follows

```ruby
EXTRA_VARS = {
  # String variable
  "variable_name" => "variable_value",
  # Number variable
  "variable_name" => 0,
  # Boolean variable
  "variable_name" => true,
  # Array variable
  "variable_name" => [ "first_element", "second_element" ],
  # Hash variable
  "variable_name" => {
    "hash_first_key" => "Hash value",
    "hash_second_key" => ["example","array"]
  }
}
```

### Altering the topology

Modify inside `Vagrantfile` the values of

- `NODE_MASTER_COUNT` number of master nodes
- `NODE_WORKER_COUNT` number of worker nodes
- `NODE_ETCD_COUNT` number of ___dedicated___ etcd nodes

Be aware that if `NODE_ETCD_COUNT` is equal to `0`, the master nodes will be used for hosting etcd

### Testing cluster scale-up / scale-down

[Change the cluster topology](#altering-the-topology) and then inside `Vagrantfile` replace

```ruby
PLAYBOOK = "cluster.yml"
```

with

```ruby
PLAYBOOK = "scale.yml"
```

then run `vagrant provison` and your cluster should be scaled

### Using a different OS

Modify inside `Vagrantfile` the values of

- `OS` the OS family (such as `debian`)
- `OS_VERSION` the OS release (such as `10`)

### Forwarding ports

Open `Vagrantfile` and edit the `FORWARD_PORTS` as follows

```ruby
FORWARD_PORTS = [
  { guest: 2375, host: 2375, host_ip: "127.0.0.1", protocol: "tcp" }
]
```

#### Explaination of port forwarding parameters

| Parameter | Explaination                  |
| :-------: | ----------------------------- |
|   guest   | Port number on the VM         |
|   host    | Port number on the host       |
|  host_ip  | IP Address to use on the host |
| protocol  | Protocol to use               |

#### Example output of port forwarding

```sh
Forwarding 2375 => 2375 on k8s-master-1
Forwarding 2376 => 2375 on k8s-master-2
Forwarding 2377 => 2375 on k8s-master-3
Forwarding 2378 => 2375 on k8s-worker-1
Forwarding 2379 => 2375 on k8s-worker-2
```

### Sharing folders

Open `Vagrantfile` and edit the `SYNCED_FOLDERS` as follows

```ruby
SYNCED_FOLDERS = [
  { from: "/tmp/cache", to: "/var/cache" }
]
```

#### Explaination of folder sharing parameters

| Parameter | Explaination     |
| :-------: | ---------------- |
|   from    | Source path      |
|    to     | Destination path |

#### Example output of folder sharing

```sh
Syncing folder /tmp/cache => /var/cache
```

### Adding additional disks

__This feature is only available using the `vagrant-libvirt` plugin__

Open `Vagrantfile` and change

- `NODE_EXTRA_DISK_COUNT` amount of extra disks available to each VM
- `NODE_EXTRA_DISK_SIZE` size in GB of each extra disk

#### Example lsblk output

`NODE_EXTRA_DISK_COUNT` was set to `2` and `NODE_EXTRA_DISK_SIZE` was set to `50`

```bash
vagrant@k8s-master-1:~$ lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
vda    254:0    0   50G  0 disk
`-vda1 254:1    0 18.6G  0 part /
vdb    254:16   0   50G  0 disk
vdc    254:32   0   50G  0 disk
```

`vdb` and `vdc` are our extra disks

### Reducing memory usage on Linux

To reduce memory usage on Linux you can use Kernel Samepage Merging that deduplicates common memory pages.

To enable it issue in a console

```sh
echo 1 | sudo tee /sys/kernel/mm/ksm/run
```

## Troubleshooting

### Machines are getting stuck at boot using the libvirt provider

This is usally due to the low amount of entropy available during the boot.

It can be fixed by adding the following line inside `~/.vagrant.d/Vagrantfile`

```ruby
Vagrant.configure("2") do |config|
  config.vm.provider :libvirt do |libvirt|
    libvirt.random :model => 'random' # Fix getting stuck at boot
  end
end
```

### Machine creation fails on Fedora using the libvirt provider

This is due to a change introduced in Fedora 30.

It can be fixed by adding the following line inside `~/.vagrant.d/Vagrantfile`

```ruby
Vagrant.configure("2") do |config|
  config.vm.provider :libvirt do |libvirt|
    # See https://fedoraproject.org/wiki/Changes/Vagrant_2.2_with_QEMU_Session
    libvirt.qemu_use_session = false
  end
end
```
