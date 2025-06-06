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

# Test collection build and install by installing our collection, emptying our repository, adding
# cluster.yml, reset.yml, and remote-node.yml files that simply point to our collection's playbooks, and then
# running the same tests as before
if [[ "${TESTCASE}" =~ "collection" ]]; then
  # Build and install collection
  ansible-galaxy collection build
  ansible-galaxy collection install kubernetes_sigs-kubespray-*.tar.gz
fi
run_playbook () {
if [[ "${TESTCASE}" =~ "collection" ]]; then
    playbook=kubernetes_sigs.kubespray.$1
else
    playbook=$1.yml
fi
shift

ansible-playbook \
    -e @tests/common_vars.yml \
    -e @tests/${TESTCASE_FILE} \
    -e local_release_dir=${PWD}/downloads \
    "$@" \
    ${playbook}
}


## START KUBESPRAY

# Create cluster
run_playbook cluster

# Repeat deployment if testing upgrade
if [ "${UPGRADE_TEST}" != "false" ]; then
  git checkout "${CI_COMMIT_SHA}"

  pip install --no-compile --no-cache-dir -r requirements.txt

  case "${UPGRADE_TEST}" in
    "basic")
        run_playbook cluster
        ;;
    "graceful")
        run_playbook upgrade-cluster
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

# Tests Cases
## Test Control Plane API
run_playbook tests/testcases/010_check-apiserver.yml
run_playbook tests/testcases/015_check-nodes-ready.yml

## Test that all nodes are Ready

if [[ ! ( "$TESTCASE" =~ "macvlan" ) ]]; then
    run_playbook tests/testcases/020_check-pods-running.yml
    run_playbook tests/testcases/030_check-network.yml
    if [[ ! ( "$TESTCASE" =~ "hardening" ) ]]; then
      # TODO: We need to remove this condition by finding alternative container
      # image instead of netchecker which doesn't work at hardening environments.
      run_playbook tests/testcases/040_check-network-adv.yml
    fi
fi

## Kubernetes conformance tests
run_playbook tests/testcases/100_check-k8s-conformance.yml

# Test node removal procedure
if [ "${REMOVE_NODE_CHECK}" = "true" ]; then
  run_playbook remove-node -e skip_confirmation=yes -e node=${REMOVE_NODE_NAME}
fi

# Clean up at the end, this is to allow stage1 tests to include cleanup test
if [ "${RESET_CHECK}" = "true" ]; then
  run_playbook reset -e reset_confirmation=yes
fi
