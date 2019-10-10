#!/bin/bash

PWD="$(pwd)/tests"

export CI_JOB_NAME="vagrant_centos7-flannel-addons"
#export CI_JOB_NAME="vagrant_coreos-canal"


export CI_PIPELINE_ID="localy"
export CI_BUILD_ID="1"
export CI_COMMIT_REF_NAME=""
export CI_PLATFORM="vagrant"
export BUILD_NUMBER="1"
export CI_BUILD_REF=
export KUBESPRAY_VERSION=


# Variables from .gitlab-ci.yaml
export FAILFASTCI_NAMESPACE='kargo-ci'
export GITLAB_REPOSITORY='kargo-ci/kubernetes-sigs-kubespray'
export ANSIBLE_FORCE_COLOR="true"
export MAGIC="ci check this"
export TEST_ID="$CI_PIPELINE_ID-$CI_BUILD_ID"
export CI_TEST_VARS="./tests/files/${CI_JOB_NAME}.yml"
#export CONTAINER_ENGINE: docker
export SSH_USER="root"
export ANSIBLE_KEEP_REMOTE_FILES="1"
export ANSIBLE_CONFIG="./tests/ansible.cfg"
export ANSIBLE_INVENTORY="${PWD}/../inventory/sample/${CI_JOB_NAME}-${BUILD_NUMBER}.ini"
export IDEMPOT_CHECK="false"
export RESET_CHECK="false"
export UPGRADE_TEST="false"
export LOG_LEVEL="-vv"

export PYPATH="/usr/bin/python"

#source ./tests/scripts/rebase.sh
#source ./tests/scripts/testcases_prepare.sh
source ./tests/scripts/testcases_run.sh
source ./tests/scripts/testcases_cleanup.sh


