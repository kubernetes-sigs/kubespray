#!/bin/bash
set -euxo pipefail

# Rebase on master to get latest changes
git config user.email "ci@kubespray.io"
git config user.name "CI"
git pull --rebase origin master
