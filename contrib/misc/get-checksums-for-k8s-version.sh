#!/bin/bash

set -e
K8S_RELEASE=${K8S_RELEASE:-"v1.21.6"}
CMDS="kubectl kubeadm kubelet"
ARCHS="arm arm64 amd64"

for cmd in $(echo ${CMDS}); do
    for arch in $(echo ${ARCHS}); do
        wget -O "${cmd}-${arch}" "https://storage.googleapis.com/kubernetes-release/release/${K8S_RELEASE}/bin/linux/${arch}/${cmd}"
    done
done

for cmd in $(echo ${CMDS}); do
    echo "Add the following lines to ${cmd}_checksums in roles/download/defaults/main.yml"
    for arch in $(echo ${ARCHS}); do
        CHECKSUM=$(sha256sum "${cmd}-${arch}" | awk '{print $1}')
        echo "  ${arch}:"
        echo "    ${K8S_RELEASE}: ${CHECKSUM}"
        rm "${cmd}-${arch}"
    done
done
