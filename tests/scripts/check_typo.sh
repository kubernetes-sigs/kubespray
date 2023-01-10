#!/bin/bash

# cd to the root directory of kubespray
cd $(dirname $0)/../../

rm ./misspell*

set -e
wget https://github.com/client9/misspell/releases/download/v0.3.4/misspell_0.3.4_linux_64bit.tar.gz
tar -zxvf ./misspell_0.3.4_linux_64bit.tar.gz
chmod 755 ./misspell
git ls-files | grep -v OWNERS_ALIASES | xargs ./misspell -error
