#!/bin/bash

set -e

# FIXME: hardcoded roles
declare -A nodes
nodes=( \
["node2"]="openstack-controller=true"
["node3"]="openstack-controller=true"
["node4"]="openstack-controller=true"
["node5"]="openstack-compute=true"
["node6"]="openstack-compute=true"
["node7"]="openstack-compute=true"
)

label_nodes() {
  all_label='openstack-compute-controller=true'
  for i in "${!nodes[@]}"
  do
    node=$i
    label=${nodes[$i]}
    kubectl get nodes $node --show-labels | grep -q "$label" || kubectl label nodes $node $label
    kubectl get nodes $node --show-labels | grep -q "$all_label" || kubectl label nodes $node $all_label
  done
}

label_nodes

