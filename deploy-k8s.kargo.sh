#!/bin/bash

INVENTORY="nodes_to_inv.py"

nodes=""
i=1
for nodeip in `cat nodes` ; do
  i=$(( $i+1 ))
  nodes+=" node${i}[ansible_ssh_host=${nodeip},ip=${nodeip}]"
done

echo "Running deployment..."
#kargo deploy -y --ansible-opts="-e @custom.yaml"
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
