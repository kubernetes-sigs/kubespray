#!/bin/bash
# I am an Ansible WANT_JSON module.

WANT_JSON=1
INPUT=$1

[ ! -r "$INPUT" ] && {
    echo "Usage: $0 <input.json>" >&2
    exit 1
}

echo "{"
echo "  \"changed\": false,"
echo "  \"msg\": \"Here is my input\","
echo "  \"input\": [$(< $INPUT)]"
echo "}"
