#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi

ansible-playbook generate-inventory.yml -e azure_resource_group="$AZURE_RESOURCE_GROUP"
