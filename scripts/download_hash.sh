#!/bin/bash
set -euo pipefail
version=$1
if [ -z "$version" ]
then
  echo "Usage: $0 <version>"
  exit 2
fi

for arch in amd64 arm64 arm
do
  for file in kubectl kubelet kubeadm
  do
    echo -n "$version $arch $file: "
    curl --fail -s "https://storage.googleapis.com/kubernetes-release/release/$version/bin/linux/$arch/$file" | shasum -a 256
  done
done
