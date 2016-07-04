#!/bin/bash
echo master > /var/tmp/role

# Some debug tools
sudo apt-get --yes update
sudo apt-get --yes upgrade
sudo apt-get --yes install screen vim telnet tcpdump python-pip traceroute iperf3 nmap ethtool curl git dnsutils

# SSH keys and config
sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo echo -e 'Host 10.*\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null' >> /root/.ssh/config
sudo chown -R root: /root/.ssh

# README
sudo echo 'cd /root/kargo ; ansible-playbook -vvv -i inv/inventory.cfg cluster.yml -u root -f 7' > /root/README
