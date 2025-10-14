#!/bin/bash

ansible-inventory $@ --list > /tmp/base_inventory.json 

NUMBER_OF_CONTROL_PLANE=$(jq < /tmp/base_inventory.json '[(.kube_control_plane.hosts | length), (.etcd.hosts | length)] | max')

export BASE_INVENTORY_FILE=/tmp/base_inventory.json
export ANSIBLE_INVENTORY=rotate_inventory.py

# Delete last control plane
INDEX=0 ansible -m debug -a var=node -e node='{{ [groups.kube_control_plane[-1], groups.etcd[-1] ] | reject("in", groups.new_etcd + groups.new_kube_control_plane) }}'  kube_control_plane[0]
# Add new control plane (last place), will be switched to first place in the first loop iteration
ROTATION=1 INDEX=1 ansible -m debug -a msg=upgrade kube_control_plane,etcd
for ((index=1;index<NUMBER_OF_CONTROL_PLANE;index++))
do
    # add new control plane / reorder
    INDEX=$index ansible -m debug -a msg=upgrade kube_control_plane,etcd
    # remove old control plane
    INDEX=$index ansible -m debug -a var=node -e node='{{ [groups.kube_control_plane[-1], groups.etcd[-1] ] | reject("in", groups.new_etcd + groups.new_kube_control_plane) }}'  kube_control_plane[0]

done

# Last iteration is done separately because we don't need a remove-node step.
INDEX=$index ansible -m debug -a msg=upgrade kube_control_plane,etcd
