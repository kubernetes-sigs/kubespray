#!/bin/bash
set -euxo pipefail

KUBESPRAY_NEXT_VERSION=2.$(( ${KUBESPRAY_VERSION:3:2} + 1 ))

# Rebase PRs on master (or release branch) to get latest changes
if [[ $CI_COMMIT_REF_NAME == pr-* ]]; then
  git config user.email "ci@kubespray.io"
  git config user.name "CI"
  if [[ -z "`git branch -a --list origin/release-$KUBESPRAY_NEXT_VERSION`" ]]; then
    git pull --rebase origin master
  else
    git pull --rebase origin release-$KUBESPRAY_NEXT_VERSION
  fi
fi
