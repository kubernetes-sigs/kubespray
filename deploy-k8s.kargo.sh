#!/bin/bash

INVENTORY="nodes_to_inv.py"

echo "Installing requirements on nodes..."
ansible-playbook -i $INVENTORY playbooks/bootstrap-nodes.yaml

echo "Running deployment..."
ansible-playbook -i $INVENTORY /root/kargo/cluster.yml -e @custom.yaml
deploy_res=$?

if [ "$deploy_res" -eq "0" ]; then
  echo "Setting up kubedns..."
  ansible-playbook -i $INVENTORY playbooks/kubedns.yaml
  echo "Setting up kubedashboard..."
  ansible-playbook -i $INVENTORY playbooks/kubedashboard.yaml
  echo "Setting up ip route work-around for DNS clusterIP availability..."
  ansible-playbook -i $INVENTORY playbooks/ipro_for_cluster_ips.yaml
fi
