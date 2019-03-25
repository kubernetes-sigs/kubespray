#!/bin/bash

#arguments
function showhelp {
   echo "$@ -r <repository_address> -m <master_ip>"
   echo "Online example: ./packages.sh --repository-address='http://192.168.20.221:8080' --master-ip='192.168.20.221'"
   echo "Airgap example: ./packages.sh --airgap --repository-address='http://192.168.20.221:8080' --master-ip='192.168.20.221'"
}

## Defaults
airgap="false"

## Deploy
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|help|--help)
        showhelp
        exit 0
        ;;
        -r|--repository-address)
        shift
        repository_address=${1}
        shift
        ;;
        -a|--airgap)
        shift
        airgap="true"
        ;;
        -m|--master-ip)
        shift
        master_ip=${1}
        shift
        ;;
    esac
done

## ubuntu

#backup orig apt
mkdir -p /etc/apt-orig
rsync -a --ignore-existing /etc/apt/ /etc/apt-orig/
rm -rf /etc/apt/sources.list.d/*

#add aptly repo to sources.list
echo "deb [arch=amd64 trusted=yes allow-insecure=yes] $repository_address bionic main" > /etc/apt/sources.list

#install ansible and pip
apt-get update
apt-get install -y --no-install-recommends python ansible sshpass python-pip
#mkdir -p ./packages/ansible_pip
#tar -C ./packages/ansible_pip -xzf ./packages/ansible_pip.tar.gz
#dpkg --install --refuse-downgrade --skip-same-version ./packages/ansible_pip/*.deb
#dpkg --install --refuse-downgrade --skip-same-version ./packages/sshpass_1.06-1_amd64.deb
#rm -rf ./packages/ansible_pip/

## ansible
sudo ansible-playbook -i inventory/sample/hosts.ini \
  --become --become-user=root \
  -e airgap=$airgap \
  -e master_ip=$master_ip \
  -e repository_address=$repository_address \
  cluster.yml

echo 'Done!'
