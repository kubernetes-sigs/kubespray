#!/bin/bash

#arguments
function showhelp {
   echo "$@ -r <repository_address> -m <master_ip>"
   echo "Online example: ./run.sh --repository-address 'http://192.168.20.221:8080' --master-ip '192.168.20.221'"
   echo "Airgap example: ./run.sh --airgap --repository-address 'http://192.168.20.221:8080' --master-ip '192.168.20.221'"
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
        #extra_vars='--extra-vars="@vars/airgap_download.yml"'
        airgap="true"
        ;;
        -m|--master-ip)
        shift
        master_ip=${1}
        shift
        ;;
    esac
done

# add aptly repo to sources.list
grep -i "$repository_address" /etc/apt/sources.list > /dev/null 2>&1
if [ $? != 0 ]; then
  mkdir -p /etc/apt-orig
  rsync -a --ignore-existing /etc/apt/ /etc/apt-orig/
  rm -rf /etc/apt/sources.list.d/*
  echo "deb [arch=amd64 trusted=yes] $repository_address bionic main" > /etc/apt/sources.list
fi

# install ansible and pip
dpkg-query -l python ansible python-pip > /dev/null 2>&1
if [ $? != 0 ]; then
  apt-get update
  apt-get install -y --no-install-recommends python ansible python-pip
fi

# run ansible playbook
sudo ansible-playbook -vvvv -i inventory/sample/hosts.ini \
  --become --become-user=root \
  -e airgap=$airgap \
  -e master_ip=$master_ip \
  -e repository_address=$repository_address \
  cluster.yml \
  #$extra_vars

echo 'Done!'
