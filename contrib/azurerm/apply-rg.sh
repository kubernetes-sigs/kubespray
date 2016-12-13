#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi

ansible-playbook generate-templates.yml

azure group deployment create -f ./.generated/network.json -g $AZURE_RESOURCE_GROUP
azure group deployment create -f ./.generated/storage.json -g $AZURE_RESOURCE_GROUP
azure group deployment create -f ./.generated/availability-sets.json -g $AZURE_RESOURCE_GROUP
azure group deployment create -f ./.generated/bastion.json -g $AZURE_RESOURCE_GROUP
azure group deployment create -f ./.generated/masters.json -g $AZURE_RESOURCE_GROUP
azure group deployment create -f ./.generated/minions.json -g $AZURE_RESOURCE_GROUP