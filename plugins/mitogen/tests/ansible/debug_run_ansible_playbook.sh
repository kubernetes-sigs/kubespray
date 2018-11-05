#!/bin/bash
# Wrap ansible-playbook, setting up some test of the test environment.

# Used by delegate_to.yml to ensure "sudo -E" preserves environment.
export I_WAS_PRESERVED=1
export MITOGEN_MAX_INTERPRETERS=3

if [ "${ANSIBLE_STRATEGY:0:7}" = "mitogen" ]
then
    EXTRA='{"is_mitogen": true}'
else
    EXTRA='{"is_mitogen": false}'
fi

exec ~/src/cpython/venv/bin/ansible-playbook -e "$EXTRA" -e ansible_python_interpreter=/Users/dmw/src/cpython/venv/bin/python2.7 "$@"
