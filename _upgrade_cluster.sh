#!/bin/sh

###ssh-agent bash
#ssh-add ~/.ssh/id_rsa

if [ -z "$1" ]; then
  echo "Usage: $0 adminname"
  exit 1
fi

d=$(date '+%Y.%m.%d_%H:%M')

export ANSIBLE_LOG_PATH=./deploy-$d.log
ansible-playbook -u "$1" -i inventory/s000000/inventory.ini upgrade-cluster.yml -b --diff
