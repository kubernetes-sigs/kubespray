#!/bin/bash
set -euxo pipefail

export PYPATH=$([[ ! "$CI_JOB_NAME" =~ "coreos" ]] && echo /usr/bin/python || echo /opt/bin/python)
echo "CI_JOB_NAME is $CI_JOB_NAME"
echo "PYPATH is $PYPATH"
pwd
ls
echo ${PWD}

export ANSIBLE_REMOTE_USER=$SSH_USER
export ANSIBLE_BECOME=true
export ANSIBLE_BECOME_USER=root

cd tests && make create-${CI_PLATFORM} -s ; cd -
ansible-playbook tests/cloud_playbooks/wait-for-ssh.yml

# CoreOS needs auto update disabled
if [[ "$CI_JOB_NAME" =~ "coreos" ]]; then
  ansible all -m raw -a 'systemctl disable locksmithd'
  ansible all -m raw -a 'systemctl stop locksmithd'
  mkdir -p /opt/bin && ln -s /usr/bin/python /opt/bin/python
fi

if [[ "$CI_JOB_NAME" =~ "opensuse" ]]; then
  # OpenSUSE needs netconfig update to get correct resolv.conf
  # See https://goinggnu.wordpress.com/2013/10/14/how-to-fix-the-dns-in-opensuse-13-1/
  ansible all -m raw -a 'netconfig update -f'
  # Auto import repo keys
  ansible all -m raw -a 'zypper --gpg-auto-import-keys refresh'
  PYPATH=/usr/bin/python3
fi

# Check out latest tag if testing upgrade
test "${UPGRADE_TEST}" != "false" && git fetch --all && git checkout "$KUBESPRAY_VERSION"
# Checkout the CI vars file so it is available
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_BUILD_REF}" tests/files/${CI_JOB_NAME}.yml

# Create cluster
ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads -e ansible_python_interpreter=${PYPATH} --limit "all:!fake_hosts" cluster.yml

# Repeat deployment if testing upgrade
if [ "${UPGRADE_TEST}" != "false" ]; then
  test "${UPGRADE_TEST}" == "basic" && PLAYBOOK="cluster.yml"
  test "${UPGRADE_TEST}" == "graceful" && PLAYBOOK="upgrade-cluster.yml"
  git checkout "${CI_BUILD_REF}"
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads -e ansible_python_interpreter=${PYPATH} --limit "all:!fake_hosts" $PLAYBOOK
fi

# Test control plane recovery
if [ "${RECOVER_CONTROL_PLANE_TEST}" != "false" ]; then
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads -e ansible_python_interpreter=${PYPATH} --limit "${RECOVER_CONTROL_PLANE_TEST_GROUPS}:!fake_hosts" -e reset_confirmation=yes reset.yml
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads -e ansible_python_interpreter=${PYPATH} -e etcd_retries=10 --limit etcd,kube-master:!fake_hosts recover-control-plane.yml
fi

# Tests Cases
## Test Master API
ansible-playbook -e ansible_python_interpreter=${PYPATH} --limit "all:!fake_hosts" tests/testcases/010_check-apiserver.yml $LOG_LEVEL

## Test that all pods are Running
ansible-playbook -e ansible_python_interpreter=${PYPATH} --limit "all:!fake_hosts" tests/testcases/015_check-pods-running.yml $LOG_LEVEL

## Test pod creation and ping between them
ansible-playbook -e ansible_python_interpreter=${PYPATH} --limit "all:!fake_hosts" tests/testcases/030_check-network.yml $LOG_LEVEL

## Advanced DNS checks
ansible-playbook -e ansible_python_interpreter=${PYPATH} --limit "all:!fake_hosts" tests/testcases/040_check-network-adv.yml $LOG_LEVEL

## Kubernetes conformance tests
ansible-playbook -i ${ANSIBLE_INVENTORY} -e ansible_python_interpreter=${PYPATH} -e @${CI_TEST_VARS} --limit "all:!fake_hosts" tests/testcases/100_check-k8s-conformance.yml $LOG_LEVEL

## Idempotency checks 1/5 (repeat deployment)
if [ "${IDEMPOT_CHECK}" = "true" ]; then
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e ansible_python_interpreter=${PYPATH} -e local_release_dir=${PWD}/downloads --limit "all:!fake_hosts" cluster.yml
fi

## Idempotency checks 2/5 (Advanced DNS checks)
if [ "${IDEMPOT_CHECK}" = "true" ]; then
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} --limit "all:!fake_hosts" tests/testcases/040_check-network-adv.yml
fi

## Idempotency checks 3/5 (reset deployment)
if [ "${IDEMPOT_CHECK}" = "true" -a "${RESET_CHECK}" = "true" ]; then
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e ansible_python_interpreter=${PYPATH} -e reset_confirmation=yes --limit "all:!fake_hosts" reset.yml
fi

## Idempotency checks 4/5 (redeploy after reset)
if [ "${IDEMPOT_CHECK}" = "true" -a "${RESET_CHECK}" = "true" ]; then
  ansible-playbook ${LOG_LEVEL} -e @${CI_TEST_VARS} -e ansible_python_interpreter=${PYPATH} -e local_release_dir=${PWD}/downloads --limit "all:!fake_hosts" cluster.yml
fi

## Idempotency checks 5/5 (Advanced DNS checks)
if [ "${IDEMPOT_CHECK}" = "true" -a "${RESET_CHECK}" = "true" ]; then
  ansible-playbook -e ansible_python_interpreter=${PYPATH}  --limit "all:!fake_hosts" tests/testcases/040_check-network-adv.yml $LOG_LEVEL
fi
