#!/bin/bash
set -euxo pipefail

cd "../inventory/$CLUSTER"
terraform destroy -auto-approve "../../contrib/terraform/$PROVIDER"
