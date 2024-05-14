#!/bin/bash
set -euxo pipefail

echo "CI_JOB_NAME is $CI_JOB_NAME"

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

# Check out latest tag if testing upgrade
test "${UPGRADE_TEST}" != "false" && git fetch --all && git checkout "$KUBESPRAY_VERSION"
# Checkout the CI vars file so it is available
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_COMMIT_SHA}" tests/files/${CI_JOB_NAME}.yml
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_COMMIT_SHA}" ${CI_TEST_REGISTRY_MIRROR}
test "${UPGRADE_TEST}" != "false" && git checkout "${CI_COMMIT_SHA}" ${CI_TEST_SETTING}


run_playbook () {
playbook=$1
shift
# We can set --limit here and still pass it as supplemental args because `--limit`  is a 'last one wins' option
ansible-playbook --limit "all:!fake_hosts" \
     $ANSIBLE_LOG_LEVEL \
    -e @${CI_TEST_SETTING} \
    -e @${CI_TEST_REGISTRY_MIRROR} \
    -e @${CI_TEST_VARS} \
    -e local_release_dir=${PWD}/downloads \
    "$@" \
    ${playbook}
}

# Create cluster
run_playbook cluster.yml

# Repeat deployment if testing upgrade
case "${UPGRADE_TEST}" in

    "basic")
        run_playbook cluster.yml
        ;;
    "graceful")
        run_playbook upgrade-cluster.yml
        ;;
    *)
        ;;
esac

# Test control plane recovery
if [ "${RECOVER_CONTROL_PLANE_TEST}" != "false" ]; then
    run_playbook reset.yml --limit "${RECOVER_CONTROL_PLANE_TEST_GROUPS}:!fake_hosts" -e reset_confirmation=yes
    run_playbook recover-control-plane.yml -e etcd_retries=10 --limit "etcd:kube_control_plane:!fake_hosts"
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
  ansible.builtin.import_playbook: kubernetes_sigs.kubespray.remove_node
EOF

fi
# Tests Cases
## Test Master API
run_playbook tests/testcases/010_check-apiserver.yml
run_playbook tests/testcases/015_check-nodes-ready.yml

## Test that all nodes are Ready

if [[ ! ( "$CI_JOB_NAME" =~ "macvlan" ) ]]; then
    run_playbook tests/testcases/020_check-pods-running.yml
    run_playbook tests/testcases/030_check-network.yml
    if [[ ! ( "$CI_JOB_NAME" =~ "hardening" ) ]]; then
      # TODO: We need to remove this condition by finding alternative container
      # image instead of netchecker which doesn't work at hardening environments.
      run_playbook tests/testcases/040_check-network-adv.yml
    fi
fi

## Kubernetes conformance tests
run_playbook tests/testcases/100_check-k8s-conformance.yml

if [ "${IDEMPOT_CHECK}" = "true" ]; then
  ## Idempotency checks 1/5 (repeat deployment)
  run_playbook cluster.yml

  ## Idempotency checks 2/5 (Advanced DNS checks)
  if [[ ! ( "$CI_JOB_NAME" =~ "hardening" ) ]]; then
      run_playbook tests/testcases/040_check-network-adv.yml
  fi

  if [ "${RESET_CHECK}" = "true" ]; then
    ## Idempotency checks 3/5 (reset deployment)
    run_playbook reset.yml -e reset_confirmation=yes

    ## Idempotency checks 4/5 (redeploy after reset)
    run_playbook cluster.yml

    ## Idempotency checks 5/5 (Advanced DNS checks)
    if [[ ! ( "$CI_JOB_NAME" =~ "hardening" ) ]]; then
        run_playbook tests/testcases/040_check-network-adv.yml
    fi
  fi
fi

# Test node removal procedure
if [ "${REMOVE_NODE_CHECK}" = "true" ]; then
  run_playbook remove-node.yml -e skip_confirmation=yes -e node=${REMOVE_NODE_NAME}
fi

# Clean up at the end, this is to allow stage1 tests to include cleanup test
if [ "${RESET_CHECK}" = "true" ]; then
  run_playbook reset.yml -e reset_confirmation=yes
fi
