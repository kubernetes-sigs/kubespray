#!/bin/bash
set -euxo pipefail

cd ..
terraform -chdir="contrib/terraform/$PROVIDER" apply -auto-approve -parallelism=1
