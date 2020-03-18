#!/bin/sh

###ssh-agent bash
#ssh-add ~/.ssh/id_rsa

if [ -z "$1" ]; then
  echo "Usage: $0 adminname"
  exit 1
fi

d=$(date '+%Y.%m.%d_%H:%M')

# if ssh access to servers only with password, then
# install sshpass on all nodes and add `-k` options 

export ANSIBLE_LOG_PATH=./deploy-$d.log
ansible-playbook -u "$1" -i inventory/s000/inventory.ini cluster.yml -b --diff
