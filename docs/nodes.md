# Adding/replacing a node

Modified from [comments in #3471](https://github.com/kubernetes-sigs/kubespray/issues/3471#issuecomment-530036084)

## Limitation: Removal of first kube-master and etcd-master

Currently you can't remove the first node in your kube-master and etcd-master list. If you still want to remove this node you have to:

### 1) Change order of current masters

Modify the order of your master list by pushing your first entry to any other position. E.g. if you want to remove `node-1` of the following example:

```yaml
  children:
    kube-master:
      hosts:
        node-1:
        node-2:
        node-3:
    kube-node:
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
    kube-master:
      hosts:
        node-2:
        node-3:
        node-1:
    kube-node:
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

run `cluster-upgrade.yml` or `cluster.yml`. Now you are good to go on with the removal.

## Adding/replacing a worker node

This should be the easiest.

### 1) Add new node to the inventory

### 2) Run `scale.yml`

You can use `--limit=node1` to limit Kubespray to avoid disturbing other nodes in the cluster.

Before using `--limit` run playbook `facts.yml` without the limit to refresh facts cache for all nodes.

### 3) Drain the node that will be removed

```sh
kubectl drain NODE_NAME
```

### 4) Run the remove-node.yml playbook

With the old node still in the inventory, run `remove-node.yml`. You need to pass `-e node=NODE_NAME` to the playbook to limit the execution to the node being removed.

### 5) Remove the node from the inventory

That's it.

## Adding/replacing a master node

### 1) Run `cluster.yml`

Append the new host to the inventory and run `cluster.yml`. You can NOT use `scale.yml` for that.

### 3) Restart kube-system/nginx-proxy

In all hosts, restart nginx-proxy pod. This pod is a local proxy for the apiserver. Kubespray will update its static config, but it needs to be restarted in order to reload.

```sh
# run in every host
docker ps | grep k8s_nginx-proxy_nginx-proxy | awk '{print $1}' | xargs docker restart
```

### 4) Remove old master nodes

With the old node still in the inventory, run `remove-node.yml`. You need to pass `-e node=NODE_NAME` to the playbook to limit the execution to the node being removed.

## Adding an etcd node

You need to make sure there are always an odd number of etcd nodes in the cluster. In such a way, this is always a replace or scale up operation. Either add two new nodes or remove an old one.

### 1) Add the new node running cluster.yml

Update the inventory and run `cluster.yml` passing `--limit=etcd,kube-master -e ignore_assert_errors=yes`.  

Run `upgrade-cluster.yml` also passing `--limit=etcd,kube-master -e ignore_assert_errors=yes`. This is necessary to update all etcd configuration in the cluster.  

At this point, you will have an even number of nodes.
Everything should still be working, and you should only have problems if the cluster decides to elect a new etcd leader before you remove a node.
Even so, running applications should continue to be available.

If you add multiple ectd nodes with one run, you might want to append `-e etcd_retries=10 retry_stagger='10'` to increase the amount of retries between each ectd node join try and
the delay between each try. Otherwise the etcd cluster might still be processing the first join and fail on subsequent nodes. `etcd_retries=10 retry_stagger='10'` might work to join 3 new nodes.

## Removing an etcd node

### 1) Remove old etcd members from the cluster runtime

Acquire a shell prompt into one of the etcd containers and use etcdctl to remove the old member. Use a etcd master that will not be removed for that.  

```sh
# list all members
etcdctl member list

# run remove for each member you want pass to remove-node.yml in step 2
etcdctl member remove MEMBER_ID
# careful!!! if you remove a wrong member you will be in trouble

# wait until you do not get a 'Failed' output from
etcdctl member list

# note: these command lines are actually much bigger, if you are not inside an etcd container, since you need to pass all certificates to etcdctl.
```

You can get into an etcd container by running `docker exec -it $(docker ps --filter "name=etcd" --format "{{.ID}}") sh` on one of the etcd masters.  

### 2) Remove an old etcd node

With the node still in the inventory, run `remove-node.yml` passing `-e node=NODE_NAME` as the name of the node that should be removed.

### 3) Make sure only remaining nodes are in your inventory

Remove `NODE_NAME` from your inventory file.

### 4) Update kubernetes and network configuration files with the valid list of etcd members

Run `cluster.yml` to regenerate the configuration files on all remaining nodes.

### 5) Shutdown the old instance

That's it.
