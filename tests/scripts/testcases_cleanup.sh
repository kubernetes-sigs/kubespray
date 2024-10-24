#!/bin/bash
set -euxo pipefail

make -C tests delete-${CI_PLATFORM} -s

if [ -d ~/.ara ] ; then
  tar czvf ${CI_PROJECT_DIR}/cluster-dump/ara.tgz ~/.ara
  rm -fr ~/.ara
fi
