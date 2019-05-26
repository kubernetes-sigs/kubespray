#!/bin/bash
set -euxo pipefail

cd ..
terraform apply -auto-approve "contrib/terraform/$PROVIDER"
