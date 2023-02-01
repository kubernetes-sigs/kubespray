# Adding/replacing a node

Modified from [comments in #3471](https://github.com/kubernetes-sigs/kubespray/issues/3471#issuecomment-530036084)

## Limitation: Removal of first kube_control_plane and etcd-master

Currently you can't remove the first node in your kube_control_plane and etcd-master list. If you still want to remove this node you have to:

### 1) Change order of current control planes

Modify the order of your control plane list by pushing your first entry to any other position. E.g. if you want to remove `node-1` of the following example:

```yaml
  children:
    kube_control_plane:
      hosts:
        node-1:
        node-2:
        node-3:
    kube_node:
      hosts:
        node-1:
        node-2:
        node-3:
    etcd:
      hosts:
        node-1:
        node-2:
        node-3:
```

change your inventory to:

```yaml
  children:
    kube_control_plane:
      hosts:
        node-2:
        node-3:
        node-1:
    kube_node:
      hosts:
        node-2:
        node-3:
        node-1:
    etcd:
      hosts:
        node-2:
        node-3:
        node-1:
```

## 2) Upgrade the cluster

run `upgrade-cluster.yml` or `cluster.yml`. Now you are good to go on with the removal.

## Adding/replacing a worker node

This should be the easiest.

### 1) Add new node to the inventory

### 2) Run `scale.yml`

You can use `--limit=NODE_NAME` to limit Kubespray to avoid disturbing other nodes in the cluster.

Before using `--limit` run playbook `facts.yml` without the limit to refresh facts cache for all nodes.

### 3) Remove an old node with remove-node.yml

With the old node still in the inventory, run `remove-node.yml`. You need to pass `-e node=NODE_NAME` to the playbook to limit the execution to the node being removed.

If the node you want to remove is not online, you should add `reset_nodes=false` and `allow_ungraceful_removal=true` to your extra-vars: `-e node=NODE_NAME -e reset_nodes=false -e allow_ungraceful_removal=true`.
Use this flag even when you remove other types of nodes like a control plane or etcd nodes.

### 4) Remove the node from the inventory

That's it.

## Adding/replacing a control plane node

### 1) Run `cluster.yml`

Append the new host to the inventory and run `cluster.yml`. You can NOT use `scale.yml` for that.

### 2) Restart kube-system/nginx-proxy

In all hosts, restart nginx-proxy pod. This pod is a local proxy for the apiserver. Kubespray will update its static config, but it needs to be restarted in order to reload.

```sh
# run in every host
docker ps | grep k8s_nginx-proxy_nginx-proxy | awk '{print $1}' | xargs docker restart
```

### 3) Remove old control plane nodes

With the old node still in the inventory, run `remove-node.yml`. You need to pass `-e node=NODE_NAME` to the playbook to limit the execution to the node being removed.
If the node you want to remove is not online, you should add `reset_nodes=false` and `allow_ungraceful_removal=true` to your extra-vars.

## Replacing a first control plane node

### 1) Change control plane nodes order in inventory

from

```ini
[kube_control_plane]
 node-1
 node-2
 node-3
```

to

```ini
[kube_control_plane]
 node-2
 node-3
 node-1
```

### 2) Remove old first control plane node from cluster

With the old node still in the inventory, run `remove-node.yml`. You need to pass `-e node=node-1` to the playbook to limit the execution to the node being removed.
If the node you want to remove is not online, you should add `reset_nodes=false` and `allow_ungraceful_removal=true` to your extra-vars.

### 3) Edit cluster-info configmap in kube-public namespace

`kubectl  edit cm -n kube-public cluster-info`

Change ip of old kube_control_plane node with ip of live kube_control_plane node (`server` field). Also, update `certificate-authority-data` field if you changed certs.

### 4) Add new control plane node

Update inventory (if needed)

Run `cluster.yml` with `--limit=kube_control_plane`

## Adding an etcd node

You need to make sure there are always an odd number of etcd nodes in the cluster. In such a way, this is always a replacement or scale up operation. Either add two new nodes or remove an old one.

### 1) Add the new node running cluster.yml

Update the inventory and run `cluster.yml` passing `--limit=etcd,kube_control_plane -e ignore_assert_errors=yes`.
If the node you want to add as an etcd node is already a worker or control plane node in your cluster, you have to remove him first using `remove-node.yml`.

Run `upgrade-cluster.yml` also passing `--limit=etcd,kube_control_plane -e ignore_assert_errors=yes`. This is necessary to update all etcd configuration in the cluster.

At this point, you will have an even number of nodes.
Everything should still be working, and you should only have problems if the cluster decides to elect a new etcd leader before you remove a node.
Even so, running applications should continue to be available.

If you add multiple etcd nodes with one run, you might want to append `-e etcd_retries=10` to increase the amount of retries between each etcd node join.
Otherwise the etcd cluster might still be processing the first join and fail on subsequent nodes. `etcd_retries=10` might work to join 3 new nodes.

### 2) Add the new node to apiserver config

In every control plane node, edit `/etc/kubernetes/manifests/kube-apiserver.yaml`. Make sure the new etcd nodes are present in the apiserver command line parameter `--etcd-servers=...`.

## Removing an etcd node

### 1) Remove an old etcd node

With the node still in the inventory, run `remove-node.yml` passing `-e node=NODE_NAME` as the name of the node that should be removed.
If the node you want to remove is not online, you should add `reset_nodes=false` and `allow_ungraceful_removal=true` to your extra-vars.

### 2) Make sure only remaining nodes are in your inventory

Remove `NODE_NAME` from your inventory file.

### 3) Update kubernetes and network configuration files with the valid list of etcd members

Run `cluster.yml` to regenerate the configuration files on all remaining nodes.

### 4) Remove the old etcd node from apiserver config

In every control plane node, edit `/etc/kubernetes/manifests/kube-apiserver.yaml`. Make sure only active etcd nodes are still present in the apiserver command line parameter `--etcd-servers=...`.

### 5) Shutdown the old instance

That's it.
