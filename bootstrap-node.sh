#!/bin/bash
echo node > /var/tmp/role

sudo apt-get --yes update
sudo apt-get --yes upgrade
sudo apt-get --yes install screen vim

sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo chown -R root: /root/.ssh

