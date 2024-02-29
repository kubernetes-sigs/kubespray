#!/bin/bash
set -e

version_from_galaxy=$(grep "^version:" galaxy.yml | awk '{print $2}')

# TODO: compute the next expected version somehow
if [[ $KUBESPRAY_VERSION == "v${version_from_galaxy}" ]]
then
	echo "Please update galaxy.yml version to match the next KUBESPRAY_VERSION."
	echo "Be sure to remove the \"v\" to adhere to semantic versioning"
	exit 1
fi
