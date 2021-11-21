#!/bin/bash
set -euxo pipefail

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

for d in $(find roles -name molecule -type d)
do
    pushd $(dirname $d)
    molecule test --all
    popd
done
