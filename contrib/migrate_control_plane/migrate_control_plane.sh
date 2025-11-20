#!/bin/bash -e

ansible-inventory "$@" --list > /tmp/base_inventory.json

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
