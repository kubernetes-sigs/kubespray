#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi

if az &>/dev/null; then
    echo "azure cli 2.0 found, using it instead of 1.0"
    ./clear-rg_2.sh "$AZURE_RESOURCE_GROUP"
else
    ansible-playbook generate-templates.yml
    azure group deployment create -g "$AZURE_RESOURCE_GROUP" -f ./.generated/clear-rg.json -m Complete
fi
