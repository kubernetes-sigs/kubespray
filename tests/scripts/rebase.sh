#!/bin/sh
set -ex

if [ "${GITHUB_BASE_REF}" ]; then
    git pull --rebase origin $GITHUB_BASE_REF
fi
