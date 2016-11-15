Travis CI test matrix
=====================

GCE instances
-------------

Here is the test matrix for the Travis CI gates:

|           Network plugin|                  OS type|               GCE region|             Nodes layout|
|-------------------------|-------------------------|-------------------------|-------------------------|
|                  flannel|       debian-8-kubespray|           europe-west1-b|                  default|
|                   calico|       debian-8-kubespray|            us-central1-c|                  default|
|                  flannel|            centos-7-sudo|             asia-east1-c|                  default|
|                   calico|            centos-7-sudo|           europe-west1-b|                  default|
|                    weave|            centos-7-sudo|            us-central1-c|                  default|
|                   calico|              rhel-7-sudo|             asia-east1-c|                  default|
|                    weave|              rhel-7-sudo|           europe-west1-b|                  default|
|                    canal|       ubuntu-1604-xenial|            us-central1-c|                  default|
|                    weave|       ubuntu-1604-xenial|             asia-east1-c|                  default|
|                    weave|            coreos-stable|           europe-west1-b|                  default|
|                    canal|            coreos-stable|               us-east1-d|                  default|
|                    canal|              rhel-7-sudo|           europe-west1-b|                 separate|
|                   calico|       ubuntu-1604-xenial|            us-central1-a|                 separate|
|                    weave|       debian-8-kubespray|               us-east1-d|                 separate|
|                   calico|            coreos-stable|             asia-east1-c|                 separate|

Where the nodes layout `default` is that is given in the example inventory file.
And the `separate` layout is when there is only node of each type, which is a kube master,
compute and etcd cluster member.

Note, the canal network plugin deploys flannel as well plus calico policy controller.

Hint: the command
```
bash scripts/gen_matrix.sh
```
will (hopefully) generate the CI test cases from the current ``.travis.yml``.


