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
and below settings, in particular regarding Ubuntu bits and
docker settings.

~~~
cat > custom.yaml << EOF
kube_api_anonymous_auth: true
kubeadm_enabled: true

# DIND Tested to work ok with below settings:
bootstrap_os: ubuntu
kubelet_fail_swap_on: false
docker_version: "18.06"
# Nodes' /dind/docker is a docker volume from the host
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
ansible-playbook --become -e ansible_ssh_user=ubuntu -i ${INVENTORY_DIR}/hosts.ini cluster.yml --extra-vars @./custom.yaml
~~~

## Resulting deployment

To get an idea on how a completed deployment looks,
from the host where you ran kubespray playbooks:

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
