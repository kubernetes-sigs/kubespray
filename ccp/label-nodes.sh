#!/bin/bash

set -e

# FIXME: hardcoded roles
declare -A nodes
nodes=( \
["node1"]="openstack-controller=true"
["node2"]="openstack-compute=true"
["node3"]="openstack-compute=true"
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

