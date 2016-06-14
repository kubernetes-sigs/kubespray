#!/bin/bash
echo node > /var/tmp/role

sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo chown -R root: /root/.ssh

