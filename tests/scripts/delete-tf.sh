#!/bin/bash
set -euxo pipefail

cd ..
terraform -chdir="contrib/terraform/$PROVIDER" destroy -auto-approve
