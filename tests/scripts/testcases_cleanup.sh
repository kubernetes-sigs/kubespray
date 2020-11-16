#!/bin/bash
set -euxo pipefail

echo "CI_PLATFORM is $CI_PLATFORM"

cd tests && make delete-${CI_PLATFORM} -s ; cd -
