#!/bin/bash
export ANSIBLE_STRATEGY=mitogen_linear
exec ./run_ansible_playbook.sh "$@"
