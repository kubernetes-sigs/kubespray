#!/bin/bash -e
#
# This is an experimental script to rotate your control plane to a new set of
# nodes, while keeping the cluster intact. However, the API **will** be
# unavailable for a short window of time during each rotation of one control
# plane.
#
# It expects:
#  - in the Ansible inventory: the 'new_etcd' and 'new_kube_control_plane' group with a count of
#    member equal to their current counterparts
#  - as arguments: the inventory-related parameters of ansible-playbook, which will be passed to
#    ansible-inventory to construct a base inventory which is then manipulated for each "rotation"
#    step
#  - in the environment:
#     - ANSIBLE_PLAYBOOKS_ARGS -> will be passed to the ansible-playbook command in each iteration.
#       Do not add --limit or --tags which are already used
#     - STEP (optionnal): this allows to restart without redoing the whole script, in case of
#       interruption or crash. See the code itself for details
#     - KUBESPRAY_ROOT: in case you're not running the script located in your kubespray directory,
#       specify its location here.
#
# How it works
#
# Basically follows [the docs on nodes operations](../../docs/operations/nodes.md), with a few
# tweaks.
#
# Basically we:
# - remove last control plane and last etcd
# - add a new control plane and etcd at the end of their respective group
# - re-order the inventory and rerun the playbook to put the new etcd / control plane first
# - remove old etcd / control plane, then add a new one, one at a time until we did all of them
#
# Between each control plane / etcd cluster modification, we update references to them in the
# workder nodes:
# - node-local load balancer to the apiserver
# - etcd client configuration for network plugin using them
#
#  !!!!!! WARNING !!!!!!!
#  This is experimental, and has only been tested on cluster using calico, with etcd datastore.

echo  '!!!!!! WARNING !!!!!!!'
echo  'This is experimental, and has only been tested on cluster using calico, with etcd datastore.'

ansible-inventory "$@" --export --list > /tmp/base_inventory.json

NUMBER_OF_CONTROL_PLANE=$(jq < /tmp/base_inventory.json '[(.kube_control_plane.hosts | length), (.etcd.hosts | length)] | max')

export BASE_INVENTORY_FILE=/tmp/base_inventory.json
export ANSIBLE_INVENTORY=$(dirname $0)/rotate_inventory.py

# TODO: remove this when switching to collection only
KUBESPRAY_ROOT=${KUBESPRAY_ROOT:-$(dirname $0)/../..}
export ANSIBLE_ROLES_PATH=$KUBESPRAY_ROOT/roles
export ANSIBLE_LIBRARY=$KUBESPRAY_ROOT/library

INDEX=0 ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/facts.yml

if [[ ${STEP:-0} == 0 ]]
then
    # Delete last control plane
    INDEX=0 ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/remove_node.yml -e node='{{ [groups.kube_control_plane[-1], groups.etcd[-1] ] | reject("in", groups.new_etcd + groups.new_kube_control_plane) }}'
    # Add new control plane (last place), will be switched to first place in the first loop iteration
    # This step is needed because Kubespray can't replace the first control plane or etcd in one
    # execution for now
    ROTATION=1 INDEX=1 ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/cluster.yml --limit 'kube_control_plane,etcd' -e upgrade_cluster_setup=true
    STEP=1
fi
for ((index=$STEP;index<NUMBER_OF_CONTROL_PLANE;index++))
do
    # add new control plane / reorder
    INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/cluster.yml --limit 'kube_control_plane,etcd' -e upgrade_cluster_setup=true
    # Update localhost loadbalancer control-plane on nodes
    # needs to update:
    # - local LB to the apiserver
    # - etcd config for network plugin such as calico
    # - container-engine config when using proxy (calico with etcd datastore breaks otherwise, probably because the cni plugin
    #   can't reach the etcd)
    INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/upgrade_cluster.yml --tags nginx,haproxy,etcd,network,container-engine --limit kube_node
    # remove old control plane
    INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/remove_node.yml -e node='{{ [groups.kube_control_plane[-1], groups.etcd[-1] ] | reject("in", groups.new_etcd + groups.new_kube_control_plane) }}'

done

# Last iteration is done separately because we don't need a remove-node step.
INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/cluster.yml --limit 'kube_control_plane,etcd' -e upgrade_cluster_setup=true
# Update localhost loadbalancer control-plane on nodes
INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/upgrade_cluster.yml --tags nginx,haproxy,etcd,network,container-engine --limit kube_node
