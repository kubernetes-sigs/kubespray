#!/bin/bash
set -euxo pipefail

curl -sL "https://releases.hashicorp.com/vagrant/2.2.4/vagrant_${VAGRANT_VERSION}_x86_64.deb" -o "/tmp/vagrant_${VAGRANT_VERSION}_x86_64.deb"
dpkg -i "/tmp/vagrant_${VAGRANT_VERSION}_x86_64.deb"
vagrant validate --ignore-provider
