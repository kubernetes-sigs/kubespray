#!/bin/bash
set -euxo pipefail

/usr/bin/python -m pip uninstall -y ansible
/usr/bin/python -m pip install -r tests/requirements.txt
ansible-galaxy collection build --force .
ansible-galaxy collection install --force kubernetes-kubespray-*.tar.gz
mkdir -p /.ssh
mkdir -p cluster-dump
mkdir -p $HOME/.ssh
ansible-playbook --version
