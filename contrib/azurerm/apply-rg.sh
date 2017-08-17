#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi

if az &>/dev/null; then
    echo "azure cli 2.0 found, using it instead of 1.0"
    ./apply-rg_2.sh "$AZURE_RESOURCE_GROUP"
elif azure &>/dev/null; then 
    ansible-playbook generate-templates.yml
    
    azure group deployment create -f ./.generated/network.json -g $AZURE_RESOURCE_GROUP
    azure group deployment create -f ./.generated/storage.json -g $AZURE_RESOURCE_GROUP
    azure group deployment create -f ./.generated/availability-sets.json -g $AZURE_RESOURCE_GROUP
    azure group deployment create -f ./.generated/bastion.json -g $AZURE_RESOURCE_GROUP
    azure group deployment create -f ./.generated/masters.json -g $AZURE_RESOURCE_GROUP
    azure group deployment create -f ./.generated/minions.json -g $AZURE_RESOURCE_GROUP
else 
    echo "Azure cli not found"
fi
