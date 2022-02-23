#!/bin/bash
set -euxo pipefail

cd tests && make delete-${CI_PLATFORM} -s ; cd -

if [ -d ~/.ara ] ; then
  tar czvf ${CI_PROJECT_DIR}/cluster-dump/ara.tgz ~/.ara
  rm -fr ~/.ara
fi
