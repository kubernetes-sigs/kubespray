#! /bin/bash

# curl -# -C - -o shebang-unit https://raw.github.com/arpinum-oss/shebang-unit/master/releases/shebang-unit
# chmod +x shebang-unit

now=$(date +"%Y%m%d%H%M%S")
mkdir -p ${PWD}/tests-results
./shebang-unit --reporters=simple,junit --output-file=${PWD}/tests-results/junit_report-${now}.xml tests
