#!/bin/bash
set -euxo pipefail

: ${ANSIBLE_MAJOR_VERSION:=2.12}

/usr/bin/python -m pip uninstall -y ansible ansible-base ansible-core
/usr/bin/python -m pip install -r tests/requirements-${ANSIBLE_MAJOR_VERSION}.txt
mkdir -p /.ssh
mkdir -p cluster-dump
mkdir -p $HOME/.ssh
ansible-playbook --version

# in some cases we may need to bring in collections or roles from ansible-galaxy
# to compensate for missing functionality in older ansible versions
if [ -f requirements-${ANSIBLE_MAJOR_VERSION}.yml ] ; then
  ansible-galaxy role install -r requirements-${ANSIBLE_MAJOR_VERSION}.yml
  ansible-galaxy collection install -r requirements-${ANSIBLE_MAJOR_VERSION}.yml
fi
