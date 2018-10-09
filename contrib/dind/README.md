# Kubespray DIND experimental setup

This ansible playbook creates local docker containers
to serve as Kubernetes "nodes", which in turn will run
"normal" Kubernetes docker containers, a mode usually
called DIND (Docker-IN-Docker).

The playbook has two roles:
- dind-host: creates the "nodes" as containers in localhost, with
  appropiate settings for DIND (privileged, volume mapping for dind
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

~~~~
# From the kubespray root dir
cd contrib/dind
pip install -r requirements.txt

ansible-playbook -i hosts dind-cluster.yaml

# Back to kubespray root
cd ../..
~~~~

NOTE: if the playbook run fails with something like below error
message, you may need to specifically set `ansible_python_interpreter`,
see `./hosts` file for an example expanded localhost entry.

~~~
failed: [localhost] (item=kube-node1) => {"changed": false, "item": "kube-node1", "msg": "Failed to import docker or docker-py - No module named requests.exceptions. Try `pip install docker` or `pip install docker-py` (Python 2.6)"}
~~~

2. Customize kubespray-dind.yaml

Note that there's coupling between above created node containers
and `kubespray-dind.yaml` settings, in particular regarding selected `node_distro`
(as set in `group_vars/all/all.yaml`), and docker settings.

~~~
$EDITOR contrib/dind/kubespray-dind.yaml
~~~

3. Prepare the inventory and run the playbook

~~~
INVENTORY_DIR=inventory/local-dind
mkdir -p ${INVENTORY_DIR}
rm -f ${INVENTORY_DIR}/hosts.ini
CONFIG_FILE=${INVENTORY_DIR}/hosts.ini /tmp/kubespray.dind.inventory_builder.sh

ansible-playbook --become -e ansible_ssh_user=debian -i ${INVENTORY_DIR}/hosts.ini cluster.yml --extra-vars @contrib/dind/kubespray-dind.yaml
~~~

NOTE: You could also test other distros without editing files by
passing `--extra-vars` as per below commandline,
replacing `DISTRO` by either `debian`, `ubuntu`, `centos`, `fedora`:

~~~
cd contrib/dind
ansible-playbook -i hosts dind-cluster.yaml --extra-vars node_distro=DISTRO

cd ../..
CONFIG_FILE=inventory/local-dind/hosts.ini /tmp/kubespray.dind.inventory_builder.sh
ansible-playbook --become -e ansible_ssh_user=DISTRO -i inventory/local-dind/hosts.ini cluster.yml --extra-vars @contrib/dind/kubespray-dind.yaml --extra-vars bootstrap_os=DISTRO
~~~

## Resulting deployment

See below to get an idea on how a completed deployment looks like,
from the host where you ran kubespray playbooks.

### node_distro: debian

~~~
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
ec0d731b489b        debian:9.5          "sh -c 'apt-get -qy …"   16 minutes ago      Up 16 minutes                           kube-node5
fc3627436d31        debian:9.5          "sh -c 'apt-get -qy …"   16 minutes ago      Up 16 minutes                           kube-node4
8a883af83c3d        debian:9.5          "sh -c 'apt-get -qy …"   16 minutes ago      Up 16 minutes                           kube-node3
2008dd7711bb        debian:9.5          "sh -c 'apt-get -qy …"   16 minutes ago      Up 16 minutes                           kube-node2
8b61d4242db2        debian:9.5          "sh -c 'apt-get -qy …"   16 minutes ago      Up 16 minutes                           kube-node1

$ docker exec kube-node1 kubectl get pod --all-namespaces
kubectl get pod --all-namespaces
NAMESPACE     NAME                                 READY     STATUS              RESTARTS   AGE
default       netchecker-agent-6snzq               1/1       Running             0          2m
default       netchecker-agent-fzskp               1/1       Running             0          2m
default       netchecker-agent-hostnet-4pzrs       1/1       Running             0          2m
default       netchecker-agent-hostnet-5cvnn       1/1       Running             0          2m
default       netchecker-agent-hostnet-hrtzq       1/1       Running             0          2m
default       netchecker-agent-hostnet-tjmmf       1/1       Running             0          2m
default       netchecker-agent-hostnet-xjk6v       1/1       Running             0          2m
default       netchecker-agent-nn64r               1/1       Running             0          2m
default       netchecker-agent-q7jqv               1/1       Running             0          2m
default       netchecker-agent-qx9j5               1/1       Running             0          2m
kube-system   coredns-78ddd56897-55m9t             1/1       Running             0          2m
kube-system   coredns-78ddd56897-s85hg             1/1       Running             0          2m
kube-system   kube-apiserver-kube-node1            1/1       Running             0          6m
kube-system   kube-apiserver-kube-node2            1/1       Running             0          6m
kube-system   kube-controller-manager-kube-node1   1/1       Running             0          5m
kube-system   kube-controller-manager-kube-node2   1/1       Running             0          5m
kube-system   kube-proxy-67v8h                     1/1       Running             0          4m
kube-system   kube-proxy-gf7pv                     1/1       Running             0          5m
kube-system   kube-proxy-hql79                     1/1       Running             0          6m
kube-system   kube-proxy-jnz52                     1/1       Running             0          6m
kube-system   kube-proxy-r6hmw                     1/1       Running             0          6m
kube-system   kube-router-cwdqs                    1/1       Running             0          6m
kube-system   kube-router-gc99s                    1/1       Running             0          5m
kube-system   kube-router-p6r2n                    1/1       Running             0          5m
kube-system   kube-router-r97dk                    1/1       Running             0          4m
kube-system   kube-router-wnwnc                    1/1       Running             0          6m
kube-system   kube-scheduler-kube-node1            1/1       Running             149        9m
kube-system   kube-scheduler-kube-node2            1/1       Running             123        0m
kube-system   nginx-proxy-kube-node3               1/1       Running             4          8m
kube-system   nginx-proxy-kube-node4               1/1       Running             4          8m
kube-system   nginx-proxy-kube-node5               1/1       Running             4          8m

$ docker exec kube-node1 curl -s http://localhost:31081/api/v1/connectivity_check
{"Message":"All 10 pods successfully reported back to the server","Absent":null,"Outdated":null}
~~~
