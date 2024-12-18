#!/bin/bash
set -euxo pipefail

make -C tests delete-${CI_PLATFORM} -s
