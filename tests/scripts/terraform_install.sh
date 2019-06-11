#!/bin/bash
set -euxo pipefail

apt-get install -y unzip
curl https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip > /tmp/terraform.zip
unzip /tmp/terraform.zip && mv ./terraform /usr/local/bin/ && terraform --version
