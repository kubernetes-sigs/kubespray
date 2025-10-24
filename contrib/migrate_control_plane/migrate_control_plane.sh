#!/bin/bash

ansible-inventory "$@" --list > /tmp/base_inventory.json

NUMBER_OF_CONTROL_PLANE=$(jq < /tmp/base_inventory.json '[(.kube_control_plane.hosts | length), (.etcd.hosts | length)] | max')

export BASE_INVENTORY_FILE=/tmp/base_inventory.json
export ANSIBLE_INVENTORY=$(dirname $0)/rotate_inventory.py

# TODO: remove this when switching to collection only
KUBESPRAY_ROOT=${KUBESPRAY_ROOT:-$(dirname $0)/../..}
export ANSIBLE_ROLES_PATH=$KUBESPRAY_ROOT/roles
export ANSIBLE_LIBRARY=$KUBESPRAY_ROOT/library

# Delete last control plane
INDEX=0 ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/remove_node.yml -e node='{{ [groups.kube_control_plane[-1], groups.etcd[-1] ] | reject("in", groups.new_etcd + groups.new_kube_control_plane) }}'
# Add new control plane (last place), will be switched to first place in the first loop iteration
ROTATION=1 INDEX=1 ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/upgrade_cluster.yml
for ((index=1;index<NUMBER_OF_CONTROL_PLANE;index++))
do
    # add new control plane / reorder
    INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/upgrade_cluster.yml
    # Update localhost loadbalancer control-plane on nodes
    ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/upgrade_cluster.yml --tags nginx,haproxy -l kube_cluster
    # remove old control plane
    INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/remove_node.yml -e node='{{ [groups.kube_control_plane[-1], groups.etcd[-1] ] | reject("in", groups.new_etcd + groups.new_kube_control_plane) }}'

done

# Last iteration is done separately because we don't need a remove-node step.
INDEX=$index ansible-playbook $ANSIBLE_PLAYBOOKS_ARGS $KUBESPRAY_ROOT/playbooks/upgrade_cluster.yml
