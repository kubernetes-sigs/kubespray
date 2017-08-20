#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi
# check if azure cli 2.0 exists else use azure cli 1.0
if az &>/dev/null; then
    ansible-playbook generate-inventory_2.yml -e azure_resource_group="$AZURE_RESOURCE_GROUP"
elif azure &>/dev/null; then
    ansible-playbook generate-inventory.yml -e azure_resource_group="$AZURE_RESOURCE_GROUP"
else
    echo "Azure cli not found"
fi
