#!/bin/sh
set -eo pipefail

VERSIONS="$@"
ARCHITECTURES="arm arm64 amd64"
DOWNLOADS="kubelet kubectl kubeadm"
DOWNLOAD_DIR="tmp/kubeadm_hasher"

if [ -z "$VERSIONS" ]; then
  echo "USAGE: $0 <versions>"
  exit 1
fi

mkdir -p ${DOWNLOAD_DIR}
for download in ${DOWNLOADS}; do
  echo -e "\n\n${download}_checksums:"
  for arch in ${ARCHITECTURES}; do
    echo -e "  ${arch}:"
    for version in ${VERSIONS}; do
      TARGET="${DOWNLOAD_DIR}/${download}-$version-$arch"
      if [ ! -f ${TARGET} ]; then
        curl -s -o ${TARGET} "https://storage.googleapis.com/kubernetes-release/release/${version}/bin/linux/${arch}/${download}"
      fi
      echo -e "    ${version}: $(sha256sum ${TARGET} | awk '{print $1}')"
    done
  done
done
echo -e "\n\nAdd these values to roles/download/defaults/main.yml"
