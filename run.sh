#!/usr/bin/env bash

set -ex

./gen_templates.py ${@}
ansible-playbook -i inventory/igz/hosts.ini cluster.yml -b --skip -tags=igz-online
ansible-playbook -i inventory/igz/hosts.ini clients.yml -b
