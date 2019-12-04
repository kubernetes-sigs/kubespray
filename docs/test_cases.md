# Node Layouts

There are four node layout types: `default`, `separate`, `ha`, and `scale`.

`default` is a non-HA two nodes setup with one separate `kube-node`
and the `etcd` group merged with the `kube-master`.

`separate` layout is when there is only node of each type, which includes
 a kube-master, kube-node, and etcd cluster member.

`ha` layout consists of two etcd nodes, two masters and a single worker node,
with role intersection.

`scale` layout can be combined with above layouts. It includes 200 fake hosts
in the Ansible inventory. This helps test TLS certificate generation at scale
to prevent regressions and profile certain long-running tasks. These nodes are
never actually deployed, but certificates are generated for them.

Note, the canal network plugin deploys flannel as well plus calico policy controller.

## GCE instances

|               Stage|      Network plugin|             OS type|          GCE region|        Nodes layout
|--------------------|--------------------|--------------------|--------------------|--------------------|
|               part1|              calico|       coreos-stable|          us-west1-b|            separate|
|               part1|               canal|  debian-8-kubespray|          us-east1-b|                  ha|
|               part1|               weave|              rhel-7|      europe-west1-b|             default|
|               part2|             flannel|            centos-7|          us-west1-a|             default|
|               part2|              calico|  debian-8-kubespray|       us-central1-b|             default|
|               part2|               canal|       coreos-stable|          us-east1-b|             default|
|             special|               canal|              rhel-7|          us-east1-b|            separate|
|             special|               weave|  ubuntu-1604-xenial|       us-central1-b|             default|
|             special|              calico|            centos-7|      europe-west1-b|            ha-scale|
|             special|               weave|        coreos-alpha|          us-west1-a|            ha-scale|

The "Stage" means a build step of the build pipeline. The steps are ordered as `part1->part2->special`.
