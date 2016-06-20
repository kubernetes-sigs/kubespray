#!/bin/bash
echo master > /var/tmp/role

# Packages
sudo apt-get --yes update
sudo apt-get --yes upgrade
sudo apt-get --yes install ansible git screen vim telnet tcpdump python-setuptools gcc python-dev python-pip libssl-dev libffi-dev software-properties-common

# Kargo-cli
sudo git clone https://github.com/kubespray/kargo-cli.git /root/kargo-cli
sudo sh -c 'cd /root/kargo-cli && python setup.py install'

# Pip
sudo pip install kpm

# k8s deploy script and config
sudo sh -c 'cp -a ~vagrant/deploy-k8s.kargo.sh /root/ && chmod 755 /root/deploy-k8s.kargo.sh'
sudo git clone https://github.com/kubespray/kargo /root/kargo
sudo cp -a ~vagrant/custom.yaml /root/kargo/custom.yaml

# SSH keys and config
sudo rm -rf /root/.ssh
sudo mv ~vagrant/ssh /root/.ssh
sudo echo -e 'Host 10.*\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null' >> /root/.ssh/config
sudo chown -R root: /root/.ssh

# Copy nodes list
sudo cp ~vagrant/nodes /root/nodes

# README
sudo echo 'cd /root/kargo ; ansible-playbook -vvv -i inv/inventory.cfg cluster.yml -u root -f 7' > /root/README
