#!/bin/bash
echo master > /var/tmp/role

# Packages
sudo apt-get --yes update
sudo apt-get --yes upgrade
sudo apt-get --yes install screen git

# SSH keys and config
sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo echo -e 'Host 10.*\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null' >> /root/.ssh/config
sudo chown -R root: /root/.ssh

