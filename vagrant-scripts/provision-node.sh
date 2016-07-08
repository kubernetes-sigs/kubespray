#!/bin/bash
echo node > /var/tmp/role

# SSH
sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo rm -f /root/.ssh/id_rsa*
sudo chown -R root: /root/.ssh

