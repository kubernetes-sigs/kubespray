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

create_network_conf() {
  if [ -f /root/cluster-topology.yaml ] ; then
    echo "/root/cluster-topology.yaml already exists"
  else
    kubectl get nodes -o go-template='{{range .items}}{{range .status.addresses}}{{if or (eq .type "ExternalIP") (eq .type "LegacyHostIP")}}{{.address}}{{print "\n"}}{{end}}{{end}}{{end}}'> /tmp/nodes
    ( echo "network:"; i=2; for ip in `cat /tmp/nodes `; do echo -e "  node$i:\n    private:\n      address: $ip"; i=$(( i+=1 )) ; done ) > /root/cluster-topology.yaml
  fi
}

assign_node_roles() {
  all_label='openstack-compute-controller=true'
  for i in "${!nodes[@]}"
  do
    node=$i
    label=${nodes[$i]}
    kubectl get nodes $node --show-labels | grep -q "$label" || kubectl label nodes $node $label
    kubectl get nodes $node --show-labels | grep -q "$all_label" || kubectl label nodes $node $all_label
  done
}

delete_namespace() {
  if kubectl get namespace | grep -q ^openstack ; then
    kubectl delete namespace openstack && while kubectl get namespace | grep -q ^openstack ; do sleep 5; done
  fi
}

deploy_microservices() {
  mcp-microservices --config-file=/root/mcp.conf --deploy-config=deploy-config.yaml deploy &> /var/log/mcp-deploy.log
}

create_network_conf
assign_node_roles
delete_namespace
deploy_microservices
