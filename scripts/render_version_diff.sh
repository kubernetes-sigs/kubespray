#!/bin/sh -e
{
    git worktree add /tmp/kubespray_old $1
    git worktree add /tmp/kubespray_new $2
    trap 'git worktree remove /tmp/kubespray_old; git worktree remove /tmp/kubespray_new; trap - EXIT; exit' EXIT TERM HUP INT
    ANSIBLE_ROLES_PATH=/tmp/kubespray_new/roles VERSION_FILE_PATH=/tmp/new_versions.json scripts/generate_versions.yml
    ANSIBLE_ROLES_PATH=/tmp/kubespray_old/roles VERSION_FILE_PATH=/tmp/old_versions.json scripts/generate_versions.yml
} 1>&2
jq -r --slurpfile old_versions /tmp/old_versions.json < /tmp/new_versions.json '(. - $old_versions[0] | sort)[] | "- **\(.[0])**: \(.[1])"'
