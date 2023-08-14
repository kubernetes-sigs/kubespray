#!/bin/bash
set -euxo pipefail

mkdir -p /.ssh
mkdir -p cluster-dump
mkdir -p $HOME/.ssh
ansible-playbook --version
