#!/bin/bash

# Author: skahlouc@skahlouc-laptop
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -o errexit
set -o pipefail

usage()
{
    cat << EOF
Create self signed certificates

Usage : $(basename $0) -f <config> [-c <cloud_provider>] [-d <ssldir>] [-g <ssl_group>]
      -h | --help         : Show this message
      -f | --config       : Openssl configuration file
      -c | --cloud        : Cloud provider (GCE, AWS or AZURE)
      -d | --ssldir       : Directory where the certificates will be installed
      -g | --sslgrp       : Group of the certificates
               
               ex : 
               $(basename $0) -f openssl.conf -c GCE -d /srv/ssl -g kube
EOF
}

# Options parsing
while (($#)); do
    case "$1" in
        -h | --help)   usage;   exit 0;;
        -f | --config) CONFIG=${2}; shift 2;;
        -c | --cloud) CLOUD=${2}; shift 2;;
        -d | --ssldir) SSLDIR="${2}"; shift 2;; 
        -g | --group) SSLGRP="${2}"; shift 2;;
        *)
            usage
            echo "ERROR : Unknown option"
            exit 3
        ;;
    esac
done

if [ -z ${CONFIG} ]; then
    echo "ERROR: the openssl configuration file is missing. option -f"
    exit 1
fi
if [ -z ${SSLDIR} ]; then
    SSLDIR="/etc/kubernetes/certs"
fi
if [ -z ${SSLGRP} ]; then
    SSLGRP="kube-cert"
fi

#echo "config=$CONFIG, cloud=$CLOUD, certdir=$SSLDIR, certgroup=$SSLGRP"

SUPPORTED_CLOUDS="GCE AWS AZURE"

# TODO: Add support for discovery on other providers?
if [ "${CLOUD}" == "GCE" ]; then
  CLOUD_IP=$(curl -s -H Metadata-Flavor:Google http://metadata.google.internal./computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
fi

if [ "${CLOUD}" == "AWS" ]; then
  CLOUD_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
fi

if [ "${CLOUD}" == "AZURE" ]; then
  CLOUD_IP=$(uname -n | awk -F. '{ print $2 }').cloudapp.net
fi

tmpdir=$(mktemp -d --tmpdir kubernetes_cacert.XXXXXX)
trap 'rm -rf "${tmpdir}"' EXIT
cd "${tmpdir}"

mkdir -p "${SSLDIR}"

# Root CA
openssl genrsa -out ca-key.pem 2048 > /dev/null 2>&1
openssl req -x509 -new -nodes -key ca-key.pem -days 10000 -out ca.pem -subj "/CN=kube-ca" > /dev/null 2>&1

# Apiserver
openssl genrsa -out apiserver-key.pem 2048 > /dev/null 2>&1
openssl req -new -key apiserver-key.pem -out apiserver.csr -subj "/CN=kube-apiserver" -config ${CONFIG} > /dev/null 2>&1
openssl x509 -req -in apiserver.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out apiserver.pem -days 365 -extensions v3_req -extfile ${CONFIG} > /dev/null 2>&1

# Nodes and Admin
for i in node admin; do
    openssl genrsa -out ${i}-key.pem 2048 > /dev/null 2>&1
    openssl req -new -key ${i}-key.pem -out ${i}.csr -subj "/CN=kube-${i}" > /dev/null 2>&1
    openssl x509 -req -in ${i}.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out ${i}.pem -days 365 > /dev/null 2>&1
done

# Install certs
mv *.pem ${SSLDIR}/
chgrp ${SSLGRP} ${SSLDIR}/*
chmod 600 ${SSLDIR}/*-key.pem
chown root:root ${SSLDIR}/*-key.pem
