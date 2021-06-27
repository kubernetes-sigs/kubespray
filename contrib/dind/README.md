# Kubespray DIND experimental setup

This ansible playbook creates local docker containers
to serve as Kubernetes "nodes", which in turn will run
"normal" Kubernetes docker containers, a mode usually
called DIND (Docker-IN-Docker).

The playbook has two roles:

- dind-host: creates the "nodes" as containers in localhost, with
  appropriate settings for DIND (privileged, volume mapping for dind
  storage, etc).
- dind-cluster: customizes each node container to have required
  system packages installed, and some utils (swapoff, lsattr)
  symlinked to /bin/true to ease mimicking a real node.

This playbook has been test with Ubuntu 16.04 as host and ubuntu:16.04
as docker images (note that dind-cluster has specific customization
for these images).

The playbook also creates a `/tmp/kubespray.dind.inventory_builder.sh`
helper (wraps up running `contrib/inventory_builder/inventory.py` with
node containers IPs and prefix).

## Deploying

See below for a complete successful run:

1. Create the node containers

```shell
# From the kubespray root dir
cd contrib/dind
pip install -r requirements.txt

ansible-playbook -i hosts dind-cluster.yaml

# Back to kubespray root
cd ../..
```

NOTE: if the playbook run fails with something like below error
message, you may need to specifically set `ansible_python_interpreter`,
see `./hosts` file for an example expanded localhost entry.

```shell
failed: [localhost] (item=kube-node1) => {"changed": false, "item": "kube-node1", "msg": "Failed to import docker or docker-py - No module named requests.exceptions. Try `pip install docker` or `pip install docker-py` (Python 2.6)"}
```

2. Customize kubespray-dind.yaml

Note that there's coupling between above created node containers
and `kubespray-dind.yaml` settings, in particular regarding selected `node_distro`
(as set in `group_vars/all/all.yaml`), and docker settings.

```shell
$EDITOR contrib/dind/kubespray-dind.yaml
```

3. Prepare the inventory and run the playbook

```shell
INVENTORY_DIR=inventory/local-dind
mkdir -p ${INVENTORY_DIR}
rm -f ${INVENTORY_DIR}/hosts.ini
CONFIG_FILE=${INVENTORY_DIR}/hosts.ini /tmp/kubespray.dind.inventory_builder.sh

ansible-playbook --become -e ansible_ssh_user=debian -i ${INVENTORY_DIR}/hosts.ini cluster.yml --extra-vars @contrib/dind/kubespray-dind.yaml
```

NOTE: You could also test other distros without editing files by
passing `--extra-vars` as per below commandline,
replacing `DISTRO` by either `debian`, `ubuntu`, `centos`, `fedora`:

```shell
cd contrib/dind
ansible-playbook -i hosts dind-cluster.yaml --extra-vars node_distro=DISTRO

cd ../..
CONFIG_FILE=inventory/local-dind/hosts.ini /tmp/kubespray.dind.inventory_builder.sh
ansible-playbook --become -e ansible_ssh_user=DISTRO -i inventory/local-dind/hosts.ini cluster.yml --extra-vars @contrib/dind/kubespray-dind.yaml --extra-vars bootstrap_os=DISTRO
```

## Resulting deployment

See below to get an idea on how a completed deployment looks like,
from the host where you ran kubespray playbooks.

### node_distro: debian

Running from an Ubuntu Xenial host:

```shell
$ uname -a
Linux ip-xx-xx-xx-xx 4.4.0-1069-aws #79-Ubuntu SMP Mon Sep 24
15:01:41 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux

$ docker ps
CONTAINER ID        IMAGE               COMMAND CREATED             STATUS              PORTS               NAMES
1835dd183b75        debian:9.5          "sh -c 'apt-get -qy …"   43 minutes ago      Up 43 minutes                           kube-node5
30b0af8d2924        debian:9.5          "sh -c 'apt-get -qy …"   43 minutes ago      Up 43 minutes                           kube-node4
3e0d1510c62f        debian:9.5          "sh -c 'apt-get -qy …"   43 minutes ago      Up 43 minutes                           kube-node3
738993566f94        debian:9.5          "sh -c 'apt-get -qy …"   44 minutes ago      Up 44 minutes                           kube-node2
c581ef662ed2        debian:9.5          "sh -c 'apt-get -qy …"   44 minutes ago      Up 44 minutes                           kube-node1

$ docker exec kube-node1 kubectl get node
NAME         STATUS   ROLES         AGE   VERSION
kube-node1   Ready    master,node   18m   v1.12.1
kube-node2   Ready    master,node   17m   v1.12.1
kube-node3   Ready    node          17m   v1.12.1
kube-node4   Ready    node          17m   v1.12.1
kube-node5   Ready    node          17m   v1.12.1

$ docker exec kube-node1 kubectl get pod --all-namespaces
NAMESPACE     NAME                                    READY   STATUS    RESTARTS   AGE
default       netchecker-agent-67489                  1/1     Running   0          2m51s
default       netchecker-agent-6qq6s                  1/1     Running   0          2m51s
default       netchecker-agent-fsw92                  1/1     Running   0          2m51s
default       netchecker-agent-fw6tl                  1/1     Running   0          2m51s
default       netchecker-agent-hostnet-8f2zb          1/1     Running   0          3m
default       netchecker-agent-hostnet-gq7ml          1/1     Running   0          3m
default       netchecker-agent-hostnet-jfkgv          1/1     Running   0          3m
default       netchecker-agent-hostnet-kwfwx          1/1     Running   0          3m
default       netchecker-agent-hostnet-r46nm          1/1     Running   0          3m
default       netchecker-agent-lxdrn                  1/1     Running   0          2m51s
default       netchecker-server-864bd4c897-9vstl      1/1     Running   0          2m40s
default       sh-68fcc6db45-qf55h                     1/1     Running   1          12m
kube-system   coredns-7598f59475-6vknq                1/1     Running   0          14m
kube-system   coredns-7598f59475-l5q5x                1/1     Running   0          14m
kube-system   kube-apiserver-kube-node1               1/1     Running   0          17m
kube-system   kube-apiserver-kube-node2               1/1     Running   0          18m
kube-system   kube-controller-manager-kube-node1      1/1     Running   0          18m
kube-system   kube-controller-manager-kube-node2      1/1     Running   0          18m
kube-system   kube-proxy-5xx9d                        1/1     Running   0          17m
kube-system   kube-proxy-cdqq4                        1/1     Running   0          17m
kube-system   kube-proxy-n64ls                        1/1     Running   0          17m
kube-system   kube-proxy-pswmj                        1/1     Running   0          18m
kube-system   kube-proxy-x89qw                        1/1     Running   0          18m
kube-system   kube-scheduler-kube-node1               1/1     Running   4          17m
kube-system   kube-scheduler-kube-node2               1/1     Running   4          18m
kube-system   kubernetes-dashboard-5db4d9f45f-548rl   1/1     Running   0          14m
kube-system   nginx-proxy-kube-node3                  1/1     Running   4          17m
kube-system   nginx-proxy-kube-node4                  1/1     Running   4          17m
kube-system   nginx-proxy-kube-node5                  1/1     Running   4          17m
kube-system   weave-net-42bfr                         2/2     Running   0          16m
kube-system   weave-net-6gt8m                         2/2     Running   0          16m
kube-system   weave-net-88nnc                         2/2     Running   0          16m
kube-system   weave-net-shckr                         2/2     Running   0          16m
kube-system   weave-net-xr46t                         2/2     Running   0          16m

$ docker exec kube-node1 curl -s http://localhost:31081/api/v1/connectivity_check
{"Message":"All 10 pods successfully reported back to the server","Absent":null,"Outdated":null}
```

## Using ./run-test-distros.sh

You can use `./run-test-distros.sh` to run a set of tests via DIND,
and excerpt from this script, to get an idea:

```shell
# The SPEC file(s) must have two arrays as e.g.
# DISTROS=(debian centos)
# EXTRAS=(
#     'kube_network_plugin=calico'
#     'kube_network_plugin=flannel'
#     'kube_network_plugin=weave'
# )
# that will be tested in a "combinatory" way (e.g. from above there'll be
# be 6 test runs), creating a sequenced <spec_filename>-nn.out with each output.
#
# Each $EXTRAS element will be whitespace split, and passed as --extra-vars
# to main kubespray ansible-playbook run.
```

See e.g. `test-some_distros-most_CNIs.env` and
`test-some_distros-kube_router_combo.env` in particular for a richer
set of CNI specific `--extra-vars` combo.
