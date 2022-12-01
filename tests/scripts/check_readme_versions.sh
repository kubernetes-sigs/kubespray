#!/bin/bash
set -e

TARGET_COMPONENTS="containerd calico cilium flannel kube-ovn kube-router weave cert-manager krew helm metallb registry cephfs-provisioner rbd-provisioner aws-ebs-csi-plugin azure-csi-plugin cinder-csi-plugin gcp-pd-csi-plugin local-path-provisioner local-volume-provisioner kube-vip ingress-nginx"

# cd to the root directory of kubespray
cd $(dirname $0)/../../

echo checking kubernetes..
version_from_default=$(grep "^kube_version:" ./roles/kubespray-defaults/defaults/main.yaml | awk '{print $2}' | sed s/\"//g)
version_from_readme=$(grep " \[kubernetes\]" ./README.md | awk '{print $3}')
if [ "${version_from_default}" != "${version_from_readme}" ]; then
	echo "The version of kubernetes is different between main.yml(${version_from_default}) and README.md(${version_from_readme})."
	echo "If the pull request updates kubernetes version, please update README.md also."
	exit 1
fi

for component in $(echo ${TARGET_COMPONENTS}); do
	echo checking ${component}..
	version_from_default=$(grep "^$(echo ${component} | sed s/"-"/"_"/g)_version:" ./roles/download/defaults/main.yml | awk '{print $2}' | sed s/\"//g | sed s/^v//)
	if [ "${version_from_default}" = "" ]; then
		version_from_default=$(grep "^$(echo ${component} | sed s/"-"/"_"/g)_version:" ./roles/kubernetes/node/defaults/main.yml | awk '{print $2}' | sed s/\"//g | sed s/^v//)
	fi
	version_from_readme=$(grep "\[${component}\]" ./README.md | grep "https" | awk '{print $3}' | sed s/^v//)
	if [ "${version_from_default}" != "${version_from_readme}" ]; then
		echo "The version of ${component} is different between main.yml(${version_from_default}) and README.md(${version_from_readme})."
		echo "If the pull request updates ${component} version, please update README.md also."
		exit 1
	fi
done

echo "Succeeded to check all components."
exit 0
