#!/bin/bash
set -euxo pipefail

cd "../inventory/$CLUSTER"
terraform apply -auto-approve "../../contrib/terraform/$PROVIDER"
