#!/bin/bash
set -e

version_from_galaxy=$(grep "^version:" galaxy.yml | awk '{print $2}')
version_from_docs=$(grep -P "^\s+version:\sv\d+\.\d+\.\d+" docs/ansible_collection.md | awk '{print $2}')

if [[ $KUBESPRAY_VERSION != "v${version_from_galaxy}" ]]
then
	echo "Please update galaxy.yml version to match the KUBESPRAY_VERSION. Be sure to remove the \"v\" to adhere"
	echo "to semenatic versioning"
	exit 1
fi

if [[ $KUBESPRAY_VERSION != "${version_from_docs}" ]]
then
	echo "Please update the documentation for Ansible collections under docs/ansible_collection.md to reflect the KUBESPRAY_VERSION"
	exit 1
fi
