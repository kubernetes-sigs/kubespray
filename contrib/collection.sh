#!/bin/bash -eux

NAMESPACE=kubernetes_sigs
COLLECTION=kubespray
MY_VER=$(grep '^version:' galaxy.yml|cut -d: -f2|sed 's/ //')

ansible-galaxy collection build --force --output-path .
# Create requirements.yml file anew for the cat.
cat >> requirements.yml << EOT
collections:
  - name: $NAMESPACE-$COLLECTION-$MY_VER.tar.gz
    type: file
    version: $MY_VER
EOT
ansible-galaxy collection install --offline --force -r requirements.yml
