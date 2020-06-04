#!/bin/bash
set -euxo pipefail

cd ..
terraform apply -auto-approve -parallelism=1 "contrib/terraform/$PROVIDER"
