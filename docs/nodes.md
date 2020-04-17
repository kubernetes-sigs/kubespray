# Adding/replacing a node

Modified from [comments in #3471](https://github.com/kubernetes-sigs/kubespray/issues/3471#issuecomment-530036084)

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

### 1) Recreate apiserver certs manually to include the new master node in the cert SAN field

For some reason, Kubespray will not update the apiserver certificate.

Edit `/etc/kubernetes/kubeadm-config.yaml`, include new host in `certSANs` list.

Use kubeadm to recreate the certs.

```sh
cd /etc/kubernetes/ssl
mv apiserver.crt apiserver.crt.old
mv apiserver.key apiserver.key.old

cd /etc/kubernetes
kubeadm init phase certs apiserver --config kubeadm-config.yaml
```

Check the certificate, new host needs to be there.

```sh
openssl x509 -text -noout -in /etc/kubernetes/ssl/apiserver.crt
```

### 2) Run `cluster.yml`

Add the new host to the inventory and run cluster.yml.

### 3) Restart kube-system/nginx-proxy

In all hosts, restart nginx-proxy pod. This pod is a local proxy for the apiserver. Kubespray will update its static config, but it needs to be restarted in order to reload.

```sh
# run in every host
docker ps | grep k8s_nginx-proxy_nginx-proxy | awk '{print $1}' | xargs docker restart
```

### 4) Remove old master nodes

If you are replacing a node, remove the old one from the inventory, and remove from the cluster runtime.

```sh
kubectl drain NODE_NAME
kubectl delete node NODE_NAME
```

After that, the old node can be safely shutdown. Also, make sure to restart nginx-proxy in all remaining nodes (step 3)

From any active master that remains in the cluster, re-upload `kubeadm-config.yaml`

```sh
kubeadm config upload from-file --config /etc/kubernetes/kubeadm-config.yaml
```

## Adding/Replacing an etcd node

You need to make sure there are always an odd number of etcd nodes in the cluster. In such a way, this is always a replace or scale up operation. Either add two new nodes or remove an old one.

### 1) Add the new node running cluster.yml

Update the inventory and run `cluster.yml` passing `--limit=etcd,kube-master -e ignore_assert_errors=yes`.

Run `upgrade-cluster.yml` also passing `--limit=etcd,kube-master -e ignore_assert_errors=yes`. This is necessary to update all etcd configuration in the cluster.

At this point, you will have an even number of nodes. Everything should still be working, and you should only have problems if the cluster decides to elect a new etcd leader before you remove a node. Even so, running applications should continue to be available.

### 2) Remove an old etcd node

With the node still in the inventory, run `remove-node.yml` passing `-e node=NODE_NAME` as the name of the node that should be removed.

### 3) Make sure the remaining etcd members have their config updated

In each etcd host that remains in the cluster:

```sh
cat /etc/etcd.env | grep ETCD_INITIAL_CLUSTER
```

Only active etcd members should be in that list.

### 4) Remove old etcd members from the cluster runtime

Acquire a shell prompt into one of the etcd containers and use etcdctl to remove the old member.

```sh
# list all members
etcdctl member list

# remove old member
etcdctl member remove MEMBER_ID
# careful!!! if you remove a wrong member you will be in trouble

# note: these command lines are actually much bigger, since you need to pass all certificates to etcdctl.
```

### 5) Make sure the apiserver config is correctly updated

In every master node, edit `/etc/kubernetes/manifests/kube-apiserver.yaml`. Make sure only active etcd nodes are still present in the apiserver command line parameter `--etcd-servers=...`.

### 6) Shutdown the old instance
