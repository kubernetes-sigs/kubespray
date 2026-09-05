#!/usr/bin/env bash
set -euo pipefail

if ! command -v ansible-playbook >/dev/null 2>&1; then
    echo "ansible-playbook is required to run this test" >&2
    exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
fixture_dir="${repo_root}/tests/files/internal_facts_unreachable"
cache_dir="$(mktemp -d)"
output_file="$(mktemp)"

cleanup() {
    rm -rf "${cache_dir}"
    rm -f "${output_file}"
}
trap cleanup EXIT

set +e
ANSIBLE_CACHE_PLUGIN=jsonfile \
ANSIBLE_CACHE_PLUGIN_CONNECTION="${cache_dir}" \
ANSIBLE_HOST_KEY_CHECKING=False \
ANSIBLE_ROLES_PATH="${fixture_dir}/roles" \
ansible-playbook \
    -i "${fixture_dir}/inventory.ini" \
    "${repo_root}/playbooks/internal_facts.yml" \
    -e '{"proxy_disable_env": {}}' >"${output_file}" 2>&1
playbook_status=$?
set -e

if [[ ${playbook_status} -eq 0 ]]; then
    cat "${output_file}"
    echo "Expected the unreachable host to make ansible-playbook return a non-zero status" >&2
    exit 1
fi

if ! grep -Rqs 'internal_facts_test_reached.*true' "${cache_dir}"; then
    cat "${output_file}"
    echo "Reachable host did not continue to fact gathering or populate the fact cache" >&2
    exit 1
fi

set +e
ANSIBLE_CACHE_PLUGIN=jsonfile \
ANSIBLE_CACHE_PLUGIN_CONNECTION="${cache_dir}" \
ANSIBLE_HOST_KEY_CHECKING=False \
ansible-playbook \
    -i "${fixture_dir}/inventory.ini" \
    "${fixture_dir}/verify_limit.yml" \
    --limit host-a >"${output_file}" 2>&1
limit_status=$?
set -e

if [[ ${limit_status} -eq 0 ]]; then
    cat "${output_file}"
    echo "Expected a limited operation to reject the excluded uncached host" >&2
    exit 1
fi

if ! grep -q 'excluded hosts are not cached:.*host-dead' "${output_file}"; then
    cat "${output_file}"
    echo "Limited operation did not report the excluded uncached host" >&2
    exit 1
fi
