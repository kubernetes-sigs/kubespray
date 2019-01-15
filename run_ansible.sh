#!/usr/bin/env bash

set -euo pipefail # bash strict mode


INOPTS=("$@")

if [[ ${#INOPTS[@]} -eq 0 ]]; then
  INOPTS=("")
fi

site="${SITEFILE:-cluster.yml}"
inventorydir="${INVENTORYDIR:-./inventory/vagrant_/}"
#inventoryver="${INVENTORYVER:-master}"
#inventoryrepo="${INVENTORYREPO:-/change/me}"
vaultfile="${VAULTFILE:-HOME/.ssh/creds/ansible_vault_changeme.txt}"

save_dir() {
  ## save current directory
  pushd . &>/dev/null
}

return_dir() {
  ## return to original directory
  popd &>/dev/null
}

inventory_checkout() {
  # do nothing if inventoryrepo is not defined
  if [[ "${inventoryrepo+DEFINED}" ]]; then

    if [[ ! -d "${inventorydir}" ]]; then
      git clone "${inventoryrepo}"
    fi

    save_dir
    cd "${inventorydir}"
    git checkout master
    git pull --rebase
    git checkout "${inventoryver}"
    git pull --rebase
    git submodule update --init --recursive
    return_dir

  fi
}

check_vaultfile() {
  if [[ -f "${vaultfile}" ]]; then
    echo "TRUE"
  else
    echo "FALSE"
  fi
}

run_ansible_playbook() {
  pipenv sync
  inventory_checkout
  
  if [[ $(check_vaultfile) == "TRUE" ]]; then
    VAULTOPTS="--vault-password-file=${vaultfile}"
  else
    VAULTOPTS=""
  fi

  export ANSIBLE_CALLBACK_WHITELIST='timer,profile_tasks'

  pipenv run \
  ansible-playbook            \
    -i "${inventorydir}"      \
    --diff                    \
    ${VAULTOPTS}              \
    "${site}"                 \
    --become                  \
    ${INOPTS[@]}
  #ansible -i "${inventorydir}" all --list-hosts
}

main() {
  run_ansible_playbook
}

time main
