# Node Layouts

There are six node layout types: `default`, `separate`, `ha`, `scale`, `all-in-one`, and `node-etcd-client`.

`default` is a non-HA two nodes setup with one separate `kube_node`
and the `etcd` group merged with the `kube_control_plane`.

`separate` layout is when there is only node of each type, which includes
 a kube_control_plane, kube_node, and etcd cluster member.

`ha` layout consists of two etcd nodes, two control planes and a single worker node,
with role intersection.

`scale` layout can be combined with above layouts (`ha-scale`, `separate-scale`). It includes 200 fake hosts
in the Ansible inventory. This helps test TLS certificate generation at scale
to prevent regressions and profile certain long-running tasks. These nodes are
never actually deployed, but certificates are generated for them.

`all-in-one` layout use a single node for with `kube_control_plane`, `etcd` and `kube_node` merged.

`node-etcd-client` layout consists of a 4 nodes cluster, all of them in `kube_node`, first 3 in `etcd` and only one `kube_control_plane`.
This is necessary to tests setups requiring that nodes are etcd clients (use of cilium as `network_plugin` for instance)

Note, the canal network plugin deploys flannel as well plus calico policy controller.

## Test cases

The [CI Matrix](/docs/developers/ci.md) displays OS, Network Plugin and Container Manager tested.

All tests are breakdown into 3 "stages" ("Stage" means a build step of the build pipeline) as follows:

- _unit_tests_: Linting, markdown, vagrant & terraform validation etc...
- _part1_: Molecule and AIO tests
- _part2_: Standard tests with different layouts and OS/Runtime/Network
- _part3_: Upgrade jobs, terraform jobs and recover control plane tests
- _special_: Other jobs (manuals)

The steps are ordered as `unit_tests->part1->part2->part3->special`.
