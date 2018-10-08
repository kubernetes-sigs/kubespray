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

2. Create custom.yaml settings

Note that there's coupling between above created node containers
and below settings, in particular regarding selected `node_distro`
(as set in `group_vars/all/all.yaml`), and docker settings.

~~~
cat > custom.yaml << EOF
kube_api_anonymous_auth: true
kubeadm_enabled: true

# DIND Tested to work ok with below settings:
kubelet_fail_swap_on: false

#bootstrap_os: ubuntu
bootstrap_os: debian

# Nodes' /dind/docker is a docker volume from the host
docker_version: latest
docker_storage_options: -s overlay2 --storage-opt overlay2.override_kernel_check=true -g /dind/docker

local_release_dir: "/usr/local/releases"
dns_mode: coredns

kube_network_plugin: weave

deploy_netchecker: True
netcheck_agent_img_repo: quay.io/l23network/k8s-netchecker-agent
netcheck_server_img_repo: quay.io/l23network/k8s-netchecker-server
netcheck_agent_tag: v1.0
netcheck_server_tag: v1.0
EOF
~~~

3. Prepare the inventory and run the playbook

~~~
INVENTORY_DIR=inventory/local-dind
mkdir -p ${INVENTORY_DIR}
rm -f ${INVENTORY_DIR}/hosts.ini
CONFIG_FILE=${INVENTORY_DIR}/hosts.ini /tmp/kubespray.dind.inventory_builder.sh
# Set ansible_ssh_user as per chosen node_distro: ubuntu or debian
ansible-playbook --become -e ansible_ssh_user=ubuntu -i ${INVENTORY_DIR}/hosts.ini cluster.yml --extra-vars @./custom.yaml
~~~

## Resulting deployment

See below to get an idea on how a completed deployment looks,
from the host where you ran kubespray playbooks.

See `group_vars/all/all.yaml` for `node_distro` setting
and `group_vars/all/distro.yaml` for supported ones.

### node_distro: ubuntu

~~~
$ docker ps
CONTAINER ID        IMAGE                                 COMMAND                  CREATED             STATUS              PORTS                       NAMES
51c13142150b        ubuntu:16.04                          "/sbin/init"             14 minutes ago      Up 14 minutes                                   kube-node5
7104c6416eec        ubuntu:16.04                          "/sbin/init"             14 minutes ago      Up 14 minutes                                   kube-node4
cce6a9c62bd0        ubuntu:16.04                          "/sbin/init"             14 minutes ago      Up 14 minutes                                   kube-node3
985b517d5884        ubuntu:16.04                          "/sbin/init"             14 minutes ago      Up 14 minutes                                   kube-node2
bdb7c4c32d56        ubuntu:16.04                          "/sbin/init"             14 minutes ago      Up 14 minutes                                   kube-node1

$ docker exec kube-node1 kubectl get pod --all-namespaces
NAMESPACE     NAME                                    READY     STATUS    RESTARTS   AGE
default       netchecker-agent-g6fdq                  1/1       Running   0          19m
default       netchecker-agent-hostnet-9bljv          1/1       Running   0          19m
default       netchecker-agent-hostnet-f9r9v          1/1       Running   0          19m
default       netchecker-agent-hostnet-jxdsb          1/1       Running   0          19m
default       netchecker-agent-hostnet-nf7gn          1/1       Running   0          19m
default       netchecker-agent-hostnet-wgfhk          1/1       Running   0          19m
default       netchecker-agent-lln49                  1/1       Running   0          19m
default       netchecker-agent-mk26w                  1/1       Running   0          19m
default       netchecker-agent-qbfq6                  1/1       Running   0          19m
default       netchecker-agent-r2hxt                  1/1       Running   0          19m
default       netchecker-server-5fbd4d84f6-wfctn      1/1       Running   0          19m
kube-system   coredns-78ddd56897-9m6c5                1/1       Running   0          20m
kube-system   coredns-78ddd56897-m7qmz                1/1       Running   0          20m
kube-system   kube-apiserver-kube-node1               1/1       Running   0          25m
kube-system   kube-apiserver-kube-node2               1/1       Running   0          24m
kube-system   kube-controller-manager-kube-node1      1/1       Running   0          25m
kube-system   kube-controller-manager-kube-node2      1/1       Running   0          24m
kube-system   kube-proxy-4425t                        1/1       Running   0          21m
kube-system   kube-proxy-925sj                        1/1       Running   0          19m
kube-system   kube-proxy-q6mw4                        1/1       Running   0          21m
kube-system   kube-proxy-qnsv6                        1/1       Running   0          20m
kube-system   kube-proxy-tnxvj                        1/1       Running   0          19m
kube-system   kube-scheduler-kube-node1               1/1       Running   147        25m
kube-system   kube-scheduler-kube-node2               1/1       Running   121        24m
kube-system   kubernetes-dashboard-789d954c6f-mm4md   1/1       Running   0          19m
kube-system   nginx-proxy-kube-node3                  1/1       Running   2          24m
kube-system   nginx-proxy-kube-node4                  1/1       Running   2          23m
kube-system   nginx-proxy-kube-node5                  1/1       Running   2          23m
kube-system   weave-net-4fwb6                         2/2       Running   0          22m
kube-system   weave-net-7gtn2                         2/2       Running   0          22m
kube-system   weave-net-blpfg                         2/2       Running   0          22m
kube-system   weave-net-dt2z8                         2/2       Running   0          22m
kube-system   weave-net-hjxm2                         2/2       Running   0          22m

$ docker exec kube-node1 curl -s http://localhost:31081/api/v1/connectivity_check
{"Message":"All 10 pods successfully reported back to the server","Absent":null,"Outdated":null}
~~~

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
