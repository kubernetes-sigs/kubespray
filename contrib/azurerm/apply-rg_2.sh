#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi

ansible-playbook generate-templates.yml

az deployment group create --template-file ./.generated/network.json -g $AZURE_RESOURCE_GROUP
az deployment group create --template-file ./.generated/storage.json -g $AZURE_RESOURCE_GROUP
az deployment group create --template-file ./.generated/availability-sets.json -g $AZURE_RESOURCE_GROUP
az deployment group create --template-file ./.generated/bastion.json -g $AZURE_RESOURCE_GROUP
az deployment group create --template-file ./.generated/masters.json -g $AZURE_RESOURCE_GROUP
az deployment group create --template-file ./.generated/minions.json -g $AZURE_RESOURCE_GROUP
