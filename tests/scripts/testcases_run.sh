#!/bin/bash
set -euxo pipefail

if [[ -v TESTCASE ]]; then
    TESTCASE_FILE=files/${TESTCASE}.yml
else
    TESTCASE_FILE=common_vars.yml
    TESTCASE=default
fi

echo "TESTCASE is $TESTCASE"

source tests/files/$TESTCASE || true

# Check out latest tag if testing upgrade
if [ "${UPGRADE_TEST}" != "false" ]; then
  git fetch --all && git checkout $(git describe --tags --abbrev=0)
  # Checkout the current tests/ directory ; even when testing old version,
  # we want the up-to-date test setup/provisionning
  git checkout "${CI_COMMIT_SHA}" -- tests/
  pip install --no-compile --no-cache-dir -r requirements.txt
fi

export ANSIBLE_BECOME=true
export ANSIBLE_BECOME_USER=root

run_playbook () {
if [[ "${TESTCASE}" =~ "collection" ]]; then
    playbook=kubernetes_sigs.kubespray.$1
    # Handle upgrade case properly
    rm -f kubernetes_sigs-kubespray-*.tar.gz
    ansible-galaxy collection build
    ansible-galaxy collection install kubernetes_sigs-kubespray-*.tar.gz
else
    playbook=$1.yml
fi
shift

ansible-playbook \
    -e @tests/common_vars.yml \
    -e @tests/${TESTCASE_FILE} \
    "$@" \
    ${playbook}
}


## START KUBESPRAY

# Create cluster
if [[ "${TESTCASE}" =~ "scale" ]]; then
    run_playbook cluster --limit '!for_scale'
    run_playbook scale --limit 'for_scale'
else
    run_playbook cluster
fi

# Repeat deployment if testing upgrade
if [ "${UPGRADE_TEST}" != "false" ]; then
  git checkout "${CI_COMMIT_SHA}"

  pip install --no-compile --no-cache-dir -r requirements.txt

  case "${UPGRADE_TEST}" in
    "basic")
        run_playbook cluster
        ;;
    "graceful")
        run_playbook upgrade_cluster
        ;;
    *)
        ;;
  esac
fi

# Test control plane recovery
if [ "${RECOVER_CONTROL_PLANE_TEST}" != "false" ]; then
    run_playbook reset --limit "${RECOVER_CONTROL_PLANE_TEST_GROUPS}" -e reset_confirmation=yes
    run_playbook recover-control-plane -e etcd_retries=10 --limit "etcd:kube_control_plane"
fi

# Run tests
ansible-playbook \
    -e @tests/common_vars.yml \
    -e @tests/${TESTCASE_FILE} \
    -e local_release_dir=${PWD}/downloads \
    tests/testcases/tests.yml

# Test node removal procedure
if [ "${REMOVE_NODE_CHECK}" = "true" ]; then
  run_playbook remove-node -e skip_confirmation=yes -e node="${REMOVE_NODE_NAME}"
fi

# Clean up at the end, this is to allow stage1 tests to include cleanup test
if [ "${RESET_CHECK}" = "true" ]; then
  run_playbook reset -e reset_confirmation=yes
fi
