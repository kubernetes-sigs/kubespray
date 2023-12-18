#!/bin/bash
set -e

version_from_galaxy=$(grep "^version:" galaxy.yml | awk '{print $2}')

if [[ $KUBESPRAY_VERSION != "v${version_from_galaxy}" ]]
then
	echo "Please update galaxy.yml version to match the KUBESPRAY_VERSION. Be sure to remove the \"v\" to adhere"
	echo "to semenatic versioning"
	exit 1
fi
