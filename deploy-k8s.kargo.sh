#!/bin/bash

custom_opts='--ansible-opts="-e @kargo/custom.yaml"'
nodes=""

i=0
for nodeip in `cat /root/nodes` ; do
  i=$(( $i+1 ))
  nodes+=" node${i}[ansible_ssh_host=${nodeip},ip=${nodeip}]"
done

kargo prepare -y --nodes $nodes
kargo deploy -y $custom_opts
deploy_res=$?

if [ "$deploy_res" -eq "0" ]; then
  echo "Setting up kubedns..."
  kpm deploy kube-system/kubedns --namespace=kube-system
fi
