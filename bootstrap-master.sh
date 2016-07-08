#!/bin/bash

# Packages
apt-get --yes update
apt-get --yes upgrade
apt-get --yes install git screen vim telnet tcpdump python-setuptools gcc python-dev python-pip libssl-dev libffi-dev software-properties-common curl

# Get ansible-2.1+, vanilla ubuntu-16.04 ansible (2.0.0.2) is broken due to https://github.com/ansible/ansible/issues/13876
ansible --version || (
  apt-add-repository -y ppa:ansible/ansible
  apt-get update
  apt-get install -y ansible
)

# Copy/create nodes list
test -f ./nodes || cp /var/tmp/nodes ./nodes

# Either pull or copy microservices repos
cp -a /var/tmp/microservices* ./ccp/ || touch /var/tmp/ccp-download

# Pull kargo
git clone https://github.com/kubespray/kargo ~/kargo
