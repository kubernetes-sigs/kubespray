#!/bin/bash

INVENTORY="/root/kargo/inventory/inventory.cfg"

echo "Createing repository and CCP images, it may take a while..."
ansible-playbook -i $INVENTORY playbooks/ccp-build.yaml

echo "Deploying up OpenStack CCP..."
ansible-playbook -i $INVENTORY playbooks/ccp-deploy.yaml
