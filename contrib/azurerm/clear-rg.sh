#!/usr/bin/env bash

set -e

AZURE_RESOURCE_GROUP="$1"

if [ "$AZURE_RESOURCE_GROUP" == "" ]; then
    echo "AZURE_RESOURCE_GROUP is missing"
    exit 1
fi

ansible-playbook generate-templates.yml

azure group deployment create -g "$AZURE_RESOURCE_GROUP" -f ./.generated/clear-rg.json -m Complete