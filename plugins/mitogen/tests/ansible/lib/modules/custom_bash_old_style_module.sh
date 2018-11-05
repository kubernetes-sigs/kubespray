#!/bin/bash
# I am an Ansible old-style module.

# This line is to encourage a UnicodeDecodeError in
# integration/runner/custom_script_interpreter.yml
#   see https://github.com/dw/mitogen/issues/195
#   £££ 
INPUT=$1

[ ! -r "$INPUT" ] && {
    echo "Usage: $0 <input_file>" >&2
    exit 1
}

echo "{"
echo "  \"changed\": false,"
echo "  \"msg\": \"Here is my input\","
echo "  \"filename\": \"$INPUT\","
echo "  \"run_via_env\": \"$RUN_VIA_ENV\","
echo "  \"input\": [\"$(cat $INPUT | tr \" \' )\"]"
echo "}"
