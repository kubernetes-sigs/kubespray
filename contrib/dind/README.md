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

See below for a complete successful run:

1. Create the node containers

~~~~
# From the kubespray root dir
cd contrib/dind
pip -r requirements.txt
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
