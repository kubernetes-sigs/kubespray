#!/bin/bash
set -euxo pipefail -o noglob

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

_PATH='roles'
_EXCLUDE=""

while [[ $# -gt 0 ]] ; do
    case $1 in
        -e|--exclude)
            _EXCLUDE="${_EXCLUDE} -not -path ${_PATH}/$2/*"
            shift
            shift
            ;;
        -i|--include)
            _PATH="${_PATH}/$2"
            shift
            shift
            ;;
        -h|--help)
            echo "Usage: molecule_run.sh [-h|--help] [-e|--exclude] [-i|--include]"
            exit 0
            ;;
    esac
done

for d in $(find ${_PATH} ${_EXCLUDE} -name molecule -type d)
do
    pushd $(dirname $d)
    molecule test --all
    popd
done
