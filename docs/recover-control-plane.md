
Recovering the control plane
============================

To recover from broken nodes in the control plane use the "recover\-control\-plane.yml" playbook.

* Backup what you can
* Provision new nodes to replace the broken ones
* Place the surviving nodes of the control plane first in the "etcd" and "kube-master" groups
* Add the new nodes below the surviving control plane nodes in the "etcd" and "kube-master" groups

Examples of what broken means in this context:

* One or more bare metal node(s) suffer from unrecoverable hardware failure
* One or more node(s) fail during patching or upgrading
* Etcd database corruption
* Other node related failures leaving your control plane degraded or nonfunctional

__Note that you need at least one functional node to be able to recover using this method.__

## If etcd quorum is intact

* Set the etcd member names of the broken node(s) in the variable "old\_etcd\_members", this variable is used to remove the broken nodes from the etcd cluster.
```old_etcd_members=etcd2,etcd3```
* If you reuse identities for your etcd nodes add the inventory names for those nodes to the variable "old\_etcds". This will remove any previously generated certificates for those nodes.
```old_etcds=etcd2.example.com,etcd3.example.com```
* If you would like to remove the broken node objects from the kubernetes cluster add their inventory names to the variable "old\_kube\_masters"
```old_kube_masters=master2.example.com,master3.example.com```

Then run the playbook with ```--limit etcd,kube-master```

When finished you should have a fully working and highly available control plane again.

## If etcd quorum is lost

* If you reuse identities for your etcd nodes add the inventory names for those nodes to the variable "old\_etcds". This will remove any previously generated certificates for those nodes.
```old_etcds=etcd2.example.com,etcd3.example.com```
* If you would like to remove the broken node objects from the kubernetes cluster add their inventory names to the variable "old\_kube\_masters"
```old_kube_masters=master2.example.com,master3.example.com```

Then run the playbook with ```--limit etcd,kube-master```

When finished you should have a fully working and highly available control plane again.

The playbook will attempt to take a snapshot from the first node in the "etcd" group and restore from that. If you would like to restore from an alternate snapshot set the path to that snapshot in the "etcd\_snapshot" variable.

```etcd_snapshot=/tmp/etcd_snapshot```

## Caveats

* The playbook has only been tested on control planes where the etcd and kube-master nodes are the same, the playbook will warn if run on a cluster with separate etcd and kube-master nodes.
* The playbook has only been tested with fairly small etcd databases.
* If your new control plane nodes have new ip addresses you may have to change settings in various places.
* There may be disruptions while running the playbook.
* There are absolutely no guarantees.

If possible try to break a cluster in the same way that your target cluster is broken and test to recover that before trying on the real target cluster.
