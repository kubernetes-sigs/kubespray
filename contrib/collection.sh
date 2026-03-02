#!/bin/bash -eux
# Install collection from source assuming dependencies are present.
# Run in SemaphoreUI this bash script can install Kubespray from the repo
NAMESPACE=kubernetes_sigs
COLLECTION=kubespray
MY_VER=$(grep '^version:' galaxy.yml|cut -d: -f2|sed 's/ //')

ansible-galaxy collection build --force --output-path .
ansible-galaxy collection install --offline --force $NAMESPACE-$COLLECTION-$MY_VER.tar.gz
