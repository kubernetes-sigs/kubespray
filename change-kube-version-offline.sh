#!/bin/bash
if [ $1 == "" ]
then
    echo "Usage: ./change-kube-ver.sh <version>";
    exit
fi
version=$1
dir="roles/kubespray-defaults/defaults/main.yaml"
sed -i "s/kube_version:.*/kube_version: ${version}/" "${dir}"
echo version has changed to  $version
