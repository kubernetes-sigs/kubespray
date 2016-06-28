#!/bin/bash

set -e

create_network_conf() {
  kubectl get nodes -o go-template='{{range .items}}{{range .status.addresses}}{{if or (eq .type "ExternalIP") (eq .type "LegacyHostIP")}}{{.address}}{{print "\n"}}{{end}}{{end}}{{end}}'> /tmp/nodes
#  ( echo "network:"; i=2; for ip in `cat /tmp/nodes `; do echo -e "  node$i:\n    private:\n      iface: eth2\n      address: $ip"; pip=`echo $ip | perl -pe 's/(\d+).(\d+).1/\${1}.\${2}.0/g'`; echo -e "    public:\n      iface: eth1\n      address: $pip" ; i=$(( i+=1 )) ;done ) > /root/cluster-topology.yaml
  ( echo "network:"; i=2; for ip in `cat /tmp/nodes `; do echo -e "  node$i:\n    private:\n      address: $ip"; i=$(( i+=1 )) ; done ) > /root/cluster-topology.yaml
}

assign_node_roles() {
  # FIXME: hardcoded roles
  kubectl label nodes node2 openstack-controller=true
  kubectl label nodes node3 openstack-controller=true
  kubectl label nodes node4 openstack-controller=true
  kubectl label nodes node5 openstack-compute=true
  kubectl label nodes node6 openstack-compute=true
  kubectl label nodes node7 openstack-compute=true
}

create_network_conf
assign_node_roles

kubectl delete namespace openstack && sleep 40
mcp-microservices --config-file=/root/mcp.conf deploy -t /root/cluster-topology.yaml

