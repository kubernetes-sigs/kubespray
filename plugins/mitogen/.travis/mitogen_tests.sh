#!/bin/bash -ex
# Run the Mitogen tests.

MITOGEN_TEST_DISTRO="${DISTRO:-debian}"
MITOGEN_LOG_LEVEL=debug PYTHONPATH=. ${TRAVIS_BUILD_DIR}/run_tests -vvv
