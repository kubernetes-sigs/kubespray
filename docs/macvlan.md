# Macvlan

## How to use it

* Enable macvlan in `group_vars/k8s-cluster/k8s-cluster.yml`

```yml
...
kube_network_plugin: macvlan
...
```

* Adjust the `macvlan_interface` in `group_vars/k8s-cluster/k8s-net-macvlan.yml` or by host in the `host.yml` file:

```yml
all:
  hosts:
    node1:
      ip: 10.2.2.1
      access_ip: 10.2.2.1
      ansible_host: 10.2.2.1
      macvlan_interface: ens5
```

## Issue encountered

* Service DNS

reply from unexpected source:

add `kube_proxy_masquerade_all: true` in `group_vars/all/all.yml`

* Disable nodelocaldns

The nodelocal dns IP is not reacheable.

Disable it in `sample/group_vars/k8s-cluster/k8s-cluster.yml`

```yml
enable_nodelocaldns: false
```
