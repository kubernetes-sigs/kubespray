#!/bin/bash

# I am an Ansible WANT_JSON module that returns the paths to its argv[0] and
# args file.

INPUT="$1"

[ ! -r "$INPUT" ] && {
    echo "Usage: $0 <input_file.json>" >&2
    exit 1
}

echo "{"
echo "  \"changed\": false,"
echo "  \"msg\": \"Here is my input\","
echo "  \"input\": [$(< $INPUT)],"
echo "  \"argv0\": \"$0\","
echo "  \"argv1\": \"$1\""
echo "}"
