#!/bin/bash
echo node > /var/tmp/role

# Some debug tools
sudo apt-get --yes update
sudo apt-get --yes upgrade
sudo apt-get --yes install screen vim telnet tcpdump python-pip traceroute iperf3 nmap ethtool curl

# Pip kpm
sudo pip install kpm

# SSH
sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo rm -f /root/.ssh/id_rsa*
sudo chown -R root: /root/.ssh

# DISABLED: switched to new box which has 100G / partition
# Setup new drive for docker
#sudo mkfs.ext4 /dev/vdb
#sudo mkdir -p /var/lib/docker
#sudo echo '/dev/vdb /var/lib/docker ext4 defaults,noatime,nodiratime 0 0' >> /etc/fstab
#sudo mount -a

