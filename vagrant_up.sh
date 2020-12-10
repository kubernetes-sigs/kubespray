#!/bin/bash
set -ve
set -o pipefail

. ./vagrant_common.sh

now_ts=$(date '+%Y_%m_%d_%H_%M')

if [ -f "$HOME/.kube/config" ]; then
  # backup old config before overwriting
  cp "$HOME/.kube/config" "$HOME/.kube/config_${now_ts?}"
fi

# Bring up vagrant
vagrant up --debug
# SSH into the master & get the kube config
vagrant ssh k8s-1 -c 'sudo cat /root/.kube/config' > $HOME/.kube/config

# Run cluster setup scripts for Akash stuff
${AKASH_DIR?}/script/setup-kind.sh crd
${AKASH_DIR?}/script/setup-kind.sh networking
