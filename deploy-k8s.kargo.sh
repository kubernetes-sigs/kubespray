#!/bin/bash

custom_opts='--ansible-opts=\"-e kargo/custom.yaml\"'
nodes=""

i=0
for nodeip in `cat /root/nodes` ; do
  i=$(( $i+1 ))
  nodes+=" node${i}[ansible_ssh_host=${nodeip},ip=${nodeip}]"
done

if [ -f kargo/inventory/inventory.cfg ] ; then
  echo "kargo/inventory/inventory.cfg already exists, if you want to recreate, pls remove it and re-run this script"
else
  echo "Preparing inventory..."
  kargo prepare -y --nodes $nodes
fi

echo "Running deployment..."
deploy_res=$?

if [ "$deploy_res" -eq "0" ]; then
  echo "Setting up kubedns..."
  kpm deploy kube-system/kubedns --namespace=kube-system
fi
