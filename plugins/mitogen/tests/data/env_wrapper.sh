#!/bin/bash
# This script exists to test the behavior of Stream.python_path being set to a
# list. It sets an environmnt variable that we can detect, then executes any
# arguments passed to it.
export EXECUTED_VIA_ENV_WRAPPER=1
if [ "${1:0:1}" == "-" ]; then
    exec "$PYTHON" "$@"
else
    export ENV_WRAPPER_FIRST_ARG="$1"
    shift
    exec "$@"
fi
