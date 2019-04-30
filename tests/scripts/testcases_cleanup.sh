#!/bin/bash
set -euxo pipefail

cd tests && make delete-${CI_PLATFORM} -s ; cd -
