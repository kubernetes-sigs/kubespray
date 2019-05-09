#!/bin/bash
set -euxo pipefail

cd ..
terraform destroy -auto-approve "contrib/terraform/$PROVIDER"
