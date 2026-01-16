#!/bin/sh -e
export ANSIBLE_COLLECTIONS_PATH="./ansible_collections"
ansible-galaxy collection build --force
ansible-galaxy collection install kubernetes_sigs-kubespray-$(grep "^version:" galaxy.yml | awk '{print $2}').tar.gz
ansible-galaxy collection list $(egrep -i '(name:\s+|namespace:\s+)' galaxy.yml | awk '{print $2}' | tr '\n' '.' | sed 's|\.$||g') | grep "^kubernetes_sigs.kubespray"
test -f ansible_collections/kubernetes_sigs/kubespray/playbooks/cluster.yml
test -f ansible_collections/kubernetes_sigs/kubespray/playbooks/reset.yml
