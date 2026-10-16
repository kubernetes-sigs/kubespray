#!/bin/sh
# Usage:
# generate_release_notes.sh <endrev> <startrev>
# defautto closest tag on current branch -> current branch
# This scripts generate the expected format for Kubespray release notes:
# release-notes tool output + components with updated versions
set -o pipefail

endrev=${1:-$(git rev-parse --abbrev-ref HEAD)}
startrev=${2:-$(git describe --tags --abbrev=0)}
ORG=kubernetes-sigs REPO=kubespray release-notes --branch $endrev --start-rev $startrev --end-rev $endrev  --dependencies=false --required-author="" --output /dev/stdout | cat
# `cat` invocation is to workaround a Linux oddity https://unix.stackexchange.com/a/716439
# TL;DR: opening /dev/stdout and writing to it does not affect the script
# stdout, in particular it does not change the current "cursor", meaning next
# writes would overwrite what we just wrote

if [ $? -eq 127 ]
then
    echo >&2 "Please install release-notes (see https://github.com/kubernetes/release/blob/master/cmd/release-notes/README.md)"
    exit 127
fi

echo "

### Components
"
$(dirname $0)/render_version_diff.sh $startrev ${UPSTREAM_REMOTE:-upstream}/$endrev
