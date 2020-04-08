#!/bin/bash
set -euxo pipefail

/usr/bin/python -m pip install -r tests/requirements.txt
mkdir -p /.ssh
mkdir -p cluster-dump
mkdir -p $HOME/.ssh
ansible-playbook --version
