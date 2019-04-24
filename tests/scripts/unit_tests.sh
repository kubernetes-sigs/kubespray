#!/bin/bash
set -euxo pipefail

export SHELLCHECK_VERSION="v0.6.0"
export ANSIBLE_INVENTORY="inventory/local-tests.cfg"
export ANSIBLE_REMOTE_USER="root"
export ANSIBLE_BECOME="true"
export ANSIBLE_BECOME_USER="root"
export ANSIBLE_VERBOSITY="3"

# Fetch shellcheck bin
curl --silent "https://storage.googleapis.com/shellcheck/shellcheck-${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" | tar -xJv
cp shellcheck-"${SHELLCHECK_VERSION}"/shellcheck /usr/bin/

# Version check
shellcheck --version
ansible-lint --version
yamllint --version

# Yamllint the repo
yamllint --strict .

# Shell check of scripts
find . -name '*.sh' -not -path './contrib/*' -print0 | xargs -0 shellcheck --severity error

# Syntax-check of playbooks
ansible-playbook --syntax-check cluster.yml
ansible-playbook --syntax-check upgrade-cluster.yml
ansible-playbook --syntax-check reset.yml
ansible-playbook --syntax-check scale.yml
ansible-playbook --syntax-check extra_playbooks/upgrade-only-k8s.yml

# Ansible-lint checks
grep -Rl '^- hosts: \|^  hosts: \|^- name: ' --include \*.yml --include \*.yaml . | parallel -j15 ansible-lint -v
