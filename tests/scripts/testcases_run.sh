#!/bin/bash
set -euxo pipefail

echo "CI_JOB_NAME is $CI_JOB_NAME"
CI_TEST_ADDITIONAL_VARS=""

if [[ "$CI_JOB_NAME" =~ "upgrade" ]]; then
  if [ "${UPGRADE_TEST}" == "false" ]; then
    echo "Job name contains 'upgrade', but UPGRADE_TEST='false'"
    exit 1
  fi
else
  if [ "${UPGRADE_TEST}" != "false" ]; then
    echo "UPGRADE_TEST!='false', but job names does not contain 'upgrade'"
    exit 1
  fi
fi

# needed for ara not to complain
export TZ=UTC

export ANSIBLE_REMOTE_USER=$SSH_USER
export ANSIBLE_BECOME=true
export ANSIBLE_BECOME_USER=root
export ANSIBLE_CALLBACK_PLUGINS="$(python -m ara.setup.callback_plugins)"

cd tests && make create-${CI_PLATFORM} -s ; cd -
ansible-playbook tests/cloud_playbooks/wait-for-ssh.yml

# Flatcar Container Linux needs auto update disabled
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
fi

if [[ "$CI_JOB_NAME" =~ "ubuntu" ]]; then
  # We need to tell ansible that ubuntu hosts are python3 only
  CI_TEST_ADDITIONAL_VARS="-e ansible_python_interpreter=/usr/bin/python3"
fi

ENABLE_040_TEST="true"
if [[ "$CI_JOB_NAME" =~ "hardening" ]]; then
  # TODO: We need to remove this condition by finding alternative container
  # image instead of netchecker which doesn't work at hardening environments.
  ENABLE_040_TEST="false"
fi

# Check out latest tag if testing upgrade
test "${UPGRADE_TEST}" != "false" && git fetch --all && git checkout "$KUBESPRAY_VERSION"
# Checkout the CI vars file so it is available
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_BUILD_REF}" tests/files/${CI_JOB_NAME}.yml
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_BUILD_REF}" ${CI_TEST_REGISTRY_MIRROR}
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_BUILD_REF}" ${CI_TEST_SETTING}

# Create cluster
ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads --limit "all:!fake_hosts" cluster.yml

# Repeat deployment if testing upgrade
if [ "${UPGRADE_TEST}" != "false" ]; then
  test "${UPGRADE_TEST}" == "basic" && PLAYBOOK="cluster.yml"
  test "${UPGRADE_TEST}" == "graceful" && PLAYBOOK="upgrade-cluster.yml"
  git checkout "${CI_BUILD_REF}"
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads --limit "all:!fake_hosts" $PLAYBOOK
fi

# Test control plane recovery
if [ "${RECOVER_CONTROL_PLANE_TEST}" != "false" ]; then
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads --limit "${RECOVER_CONTROL_PLANE_TEST_GROUPS}:!fake_hosts" -e reset_confirmation=yes reset.yml
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads -e etcd_retries=10 --limit etcd,kube_control_plane:!fake_hosts recover-control-plane.yml
fi

# Test collection build and install by installing our collection, emptying our repository, adding
# cluster.yml, reset.yml, and remote-node.yml files that simply point to our collection's playbooks, and then
# running the same tests as before
if [[ "${CI_JOB_NAME}" =~ "collection" ]]; then
  # Build and install collection
  ansible-galaxy collection build
  ansible-galaxy collection install kubernetes_sigs-kubespray-$(grep "^version:" galaxy.yml | awk '{print $2}').tar.gz

  # Simply remove all of our files and directories except for our tests directory
  # to be absolutely certain that none of our playbooks or roles
  # are interfering with our collection
  find -maxdepth 1 ! -name tests -exec rm -rfv {} \;

  # Write cluster.yml
cat > cluster.yml <<EOF
- name: Install Kubernetes
  ansible.builtin.import_playbook: kubernetes_sigs.kubespray.cluster
EOF

  # Write reset.yml
cat > reset.yml <<EOF
- name: Remove Kubernetes
  ansible.builtin.import_playbook: kubernetes_sigs.kubespray.reset
EOF

  # Write remove-node.yml
cat > remove-node.yml <<EOF
- name: Remove node from Kubernetes
  ansible.builtin.import_playbook: kubernetes_sigs.kubespray.remote-node
EOF

fi

# Tests Cases
## Test Master API
ansible-playbook --limit "all:!fake_hosts" -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} tests/testcases/010_check-apiserver.yml $ANSIBLE_LOG_LEVEL

## Test that all nodes are Ready
ansible-playbook --limit "all:!fake_hosts" -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} tests/testcases/015_check-nodes-ready.yml $ANSIBLE_LOG_LEVEL

## Test that all pods are Running
ansible-playbook --limit "all:!fake_hosts" -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} tests/testcases/020_check-pods-running.yml $ANSIBLE_LOG_LEVEL

## Test pod creation and ping between them
ansible-playbook --limit "all:!fake_hosts" -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} tests/testcases/030_check-network.yml $ANSIBLE_LOG_LEVEL

## Advanced DNS checks
if [ "${ENABLE_040_TEST}" = "true" ]; then
  ansible-playbook --limit "all:!fake_hosts" -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} tests/testcases/040_check-network-adv.yml $ANSIBLE_LOG_LEVEL
fi

## Kubernetes conformance tests
ansible-playbook -i ${ANSIBLE_INVENTORY} -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} --limit "all:!fake_hosts" tests/testcases/100_check-k8s-conformance.yml $ANSIBLE_LOG_LEVEL

if [ "${IDEMPOT_CHECK}" = "true" ]; then
  ## Idempotency checks 1/5 (repeat deployment)
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} ${CI_TEST_ADDITIONAL_VARS} -e @${CI_TEST_VARS} -e local_release_dir=${PWD}/downloads --limit "all:!fake_hosts" cluster.yml

  ## Idempotency checks 2/5 (Advanced DNS checks)
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} --limit "all:!fake_hosts" tests/testcases/040_check-network-adv.yml

  if [ "${RESET_CHECK}" = "true" ]; then
    ## Idempotency checks 3/5 (reset deployment)
    ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR}  -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} -e reset_confirmation=yes --limit "all:!fake_hosts" reset.yml

    ## Idempotency checks 4/5 (redeploy after reset)
    ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} -e local_release_dir=${PWD}/downloads --limit "all:!fake_hosts" cluster.yml

    ## Idempotency checks 5/5 (Advanced DNS checks)
    ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR} -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} --limit "all:!fake_hosts" tests/testcases/040_check-network-adv.yml
  fi
fi

# Test node removal procedure
if [ "${REMOVE_NODE_CHECK}" = "true" ]; then
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR}  -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} -e skip_confirmation=yes -e node=${REMOVE_NODE_NAME} --limit "all:!fake_hosts" remove-node.yml
fi

# Clean up at the end, this is to allow stage1 tests to include cleanup test
if [ "${RESET_CHECK}" = "true" ]; then
  ansible-playbook ${ANSIBLE_LOG_LEVEL} -e @${CI_TEST_SETTING} -e @${CI_TEST_REGISTRY_MIRROR}  -e @${CI_TEST_VARS} ${CI_TEST_ADDITIONAL_VARS} -e reset_confirmation=yes --limit "all:!fake_hosts" reset.yml
fi
