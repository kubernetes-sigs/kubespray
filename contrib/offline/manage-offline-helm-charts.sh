#!/bin/bash

OPTION=$1
CURRENT_DIR=$(cd $(dirname $0); pwd)
TEMP_DIR="${CURRENT_DIR}/temp"

CHART_TAR_FILE="${CURRENT_DIR}/helm-charts.tar.gz"
CHART_DIR="${CURRENT_DIR}/helm-charts"
HELM_LIST="${HELM_LIST:-${TEMP_DIR}/helm.list}"

# Convert to absolute path if relative
if [[ ! "${HELM_LIST}" = /* ]]; then
	HELM_LIST="${CURRENT_DIR}/${HELM_LIST}"
fi

CHART_LIST="${CHART_DIR}/helm-list.txt"
REGISTRY_PORT=${REGISTRY_PORT:-5000}
REGISTRY_HOST="${REGISTRY_HOST:-localhost}"
DESTINATION_REGISTRY="${DESTINATION_REGISTRY:-${REGISTRY_HOST}}"

function create_helm_chart_tar() {
	set -e

	if [ ! -f "${HELM_LIST}" ]; then
		echo "${HELM_LIST} is not a file"
		exit 1
	fi

	rm -f  ${CHART_TAR_FILE}
	rm -rf ${CHART_DIR}
	mkdir  ${CHART_DIR}
	cd     ${CHART_DIR}

	if ! command -v helm &> /dev/null; then
		echo "Error: helm command not found"
		exit 1
	fi

	while read -r chart_url || [[ -n "${chart_url}" ]]; do
		[[ -z "${chart_url}" || "${chart_url}" =~ ^# ]] && continue

		chart_name=$(echo "${chart_url}" | sed 's@.*/@@' | sed 's/:.*//')
		chart_version=$(echo "${chart_url}" | sed 's@.*:@@')
		FILE_NAME="${chart_name}-${chart_version}.tgz"

		echo "Downloading: ${chart_url}"
		helm pull "${chart_url}" --untar=false

	_chart_ref=$(echo "${chart_url}" | sed 's@^oci://@@')
		echo "${FILE_NAME}  ${_chart_ref}" >> ${CHART_LIST}
		echo "Processed: ${chart_url} -> ${FILE_NAME}"
	done < "${HELM_LIST}"

	cd ..
	tar -zcvf ${CHART_TAR_FILE} ./helm-charts
	rm -rf ${CHART_DIR}

	echo ""
	echo "${CHART_TAR_FILE} is created to contain your Helm charts."
	echo "Please keep this file and bring it to your offline environment."
}

function register_helm_charts() {
	if [ ! -f ${CHART_TAR_FILE} ]; then
		echo "${CHART_TAR_FILE} should exist."
		exit 1
	fi

	if [ ! -f ${CHART_LIST} ]; then
		echo "${CHART_LIST} should exist."
		exit 1
	fi

	mkdir -p ${TEMP_DIR}
	rm -rf "${TEMP_DIR}/helm-charts" 2>/dev/null || true
	tar -zxvf ${CHART_TAR_FILE} -C ${TEMP_DIR}

	if ! command -v helm &> /dev/null; then
		echo "Error: helm command not found"
		exit 1
	fi

	LEGACY_CHART_DIR="${TEMP_DIR}/helm-charts"
	if [[ -d "${LEGACY_CHART_DIR}" && "${LEGACY_CHART_DIR}" != "${CHART_DIR}" ]]; then
		rm -rf "${CHART_DIR}"
		mv "${LEGACY_CHART_DIR}" "${CHART_DIR}"
	fi

	cd "${CHART_DIR}"

	while read -r line; do
		file_name=$(echo "${line}" | awk '{print $1}')
		chart_url=$(echo "${line}" | awk '{print $2}')
		
		chart_ref="${chart_url}"
		if [[ "${chart_url}" =~ ^oci:// ]]; then
			chart_ref=$(echo "${chart_url}" | sed 's@^oci://@@')
		fi

		raw_chart=$(echo "${chart_ref}" | sed 's@:[^:]*$@@')
		if [[ "${DESTINATION_REGISTRY}" == "localhost" ||("${DESTINATION_REGISTRY}" == "${REGISTRY_HOST}" && ("${REGISTRY_HOST}" == "localhost" || "${REGISTRY_HOST}" == "127.0.0.1")) ]]; then
			helm push "${file_name}" "oci://${DESTINATION_REGISTRY}:${REGISTRY_PORT}/${raw_chart}" --plain-http
		else
			helm push "${file_name}" "oci://${DESTINATION_REGISTRY}:${REGISTRY_PORT}/${raw_chart}"
		fi
	done <<< "$(cat ${CHART_LIST})"

	echo "Succeeded to register Helm charts to local registry."
}

if [ "${OPTION}" == "create" ]; then
	create_helm_chart_tar
elif [ "${OPTION}" == "register" ]; then
	register_helm_charts
else
	echo "This script has two features:"
	echo "(1) Get Helm charts from list and create tar archive"
	echo "(2) Deploy local Helm registry and register the charts to the registry."
	echo ""
	echo "Step(1) should be done online site as a preparation, then we bring"
	echo "the gotten charts to the target offline environment."
	echo "Then we will run step(2) for registering the charts to local registry."
	echo ""
	echo "${CHART_TAR_FILE} is created to contain your Helm charts."
	echo "Please keep this file and bring it to your offline environment."
	echo ""
	echo "Step(1) can be operated with:"
	echo " $ ./manage-offline-helm-charts.sh   create"
	echo ""
	echo "Step(2) can be operated with:"
	echo " $ ./manage-offline-helm-charts.sh   register"
	echo ""
	echo "Please specify 'create' or 'register'."
	echo ""
	exit 1
fi
