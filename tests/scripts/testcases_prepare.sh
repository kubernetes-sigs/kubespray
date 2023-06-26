#!/bin/bash
set -euxo pipefail

/usr/bin/python -m pip uninstall -y ansible ansible-base ansible-core
/usr/bin/python -m pip install -r tests/requirements.txt
ansible-galaxy install -r tests/requirements.yml
mkdir -p /.ssh
mkdir -p cluster-dump
mkdir -p $HOME/.ssh
ansible-playbook --version
