#!/bin/sh
set -eo pipefail

VERSION="${1}"
ARCHITECTURES="arm arm64 amd64"
DOWNLOADS="hyperkube kubeadm"

if [ -z $VERSION ]; then
  echo "USAGE: ./kubeadm_hasher.sh <version>"
  exit 1
fi

DOWNLOAD_DIR="tmp/kubeadm_hasher"
mkdir -p ${DOWNLOAD_DIR}

for download in ${DOWNLOADS}; do
  echo "\n\nChecksums for ${download}:"
  for arch in ${ARCHITECTURES}; do
    TARGET="${DOWNLOAD_DIR}/${download}-$VERSION-$arch"
    if [ ! -f ${TARGET} ]; then
      curl -s -o ${TARGET} "https://storage.googleapis.com/kubernetes-release/release/${VERSION}/bin/linux/${arch}/${download}"
    fi
    echo "  ${arch}:\n    ${VERSION}: $(sha256sum ${TARGET} | awk '{print $1}')"
  done
done

echo "\n\nAdd these values to roles/download/defaults/main.yml and extra_playbooks/roles/download/defaults/main.yml"
echo "You may want to clear your ${DOWNLOAD_DIR} directory"
