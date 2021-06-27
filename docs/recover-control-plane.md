
# Recovering the control plane

To recover from broken nodes in the control plane use the "recover\-control\-plane.yml" playbook.

* Backup what you can
* Provision new nodes to replace the broken ones
* Place the surviving nodes of the control plane first in the "etcd" and "kube\_control\_plane" groups
* Add the new nodes below the surviving control plane nodes in the "etcd" and "kube\_control\_plane" groups

Examples of what broken means in this context:

* One or more bare metal node(s) suffer from unrecoverable hardware failure
* One or more node(s) fail during patching or upgrading
* Etcd database corruption
* Other node related failures leaving your control plane degraded or nonfunctional

__Note that you need at least one functional node to be able to recover using this method.__

## Runbook

* Move any broken etcd nodes into the "broken\_etcd" group, make sure the "etcd\_member\_name" variable is set.
* Move any broken master nodes into the "broken\_kube\_control\_plane" group.

Then run the playbook with ```--limit etcd,kube_control_plane``` and increase the number of ETCD retries by setting ```-e etcd_retries=10``` or something even larger. The amount of retries required is difficult to predict.

When finished you should have a fully working control plane again.

## Recover from lost quorum

The playbook attempts to figure out it the etcd quorum is intact. If quorum is lost it will attempt to take a snapshot from the first node in the "etcd" group and restore from that. If you would like to restore from an alternate snapshot set the path to that snapshot in the "etcd\_snapshot" variable.

```-e etcd_snapshot=/tmp/etcd_snapshot```

## Caveats

* The playbook has only been tested with fairly small etcd databases.
* If your new control plane nodes have new ip addresses you may have to change settings in various places.
* There may be disruptions while running the playbook.
* There are absolutely no guarantees.

If possible try to break a cluster in the same way that your target cluster is broken and test to recover that before trying on the real target cluster.
