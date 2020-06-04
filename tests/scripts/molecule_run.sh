#!/bin/bash
set -euxo pipefail

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

for d in $(find roles -name molecule -type d)
do
    cd $(dirname $d)
    molecule test --all
    cd -
done