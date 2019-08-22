#!/bin/sh

###ssh-agent bash
#ssh-add ~/.ssh/id_rsa

if [ -z "$1" ]; then
  echo "Usage: $0 adminname"
  exit 1
fi

d=$(date '+%Y.%m.%d_%H:%M')
K=-k
T=$(which sshpass 2>/dev/null)

if [ -z "$T" ]; then
  echo "sshpass not found, disable --ask-password"
  K=""
fi

export ANSIBLE_LOG_PATH=./deploy-$d.log
ansible-playbook -u "$1" $K -i inventory/s000/inventory.ini cluster.yml -b --diff
