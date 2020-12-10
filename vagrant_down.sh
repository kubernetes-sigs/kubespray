#!/bin/bash
set -ve
set -o pipefail

. ./vagrant_common.sh

vagrant destroy --debug --force
