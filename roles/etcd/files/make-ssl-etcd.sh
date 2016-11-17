#!/bin/bash

# Author: Smana smainklh@gmail.com
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

Usage : $(basename $0) -f <config> [-d <ssldir>]
      -h | --help         : Show this message
      -f | --config       : Openssl configuration file
      -d | --ssldir       : Directory where the certificates will be installed

               ex :
               $(basename $0) -f openssl.conf -d /srv/ssl
EOF
}

# Options parsing
while (($#)); do
    case "$1" in
        -h | --help)   usage;   exit 0;;
        -f | --config) CONFIG=${2}; shift 2;;
        -d | --ssldir) SSLDIR="${2}"; shift 2;;
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
    SSLDIR="/etc/ssl/etcd"
fi

tmpdir=$(mktemp -d /tmp/etcd_cacert.XXXXXX)
trap 'rm -rf "${tmpdir}"' EXIT
cd "${tmpdir}"

mkdir -p "${SSLDIR}"

# Root CA
openssl genrsa -out ca-key.pem 2048 > /dev/null 2>&1
openssl req -x509 -new -nodes -key ca-key.pem -days 10000 -out ca.pem -subj "/CN=etcd-ca" > /dev/null 2>&1

# ETCD member
openssl genrsa -out member-key.pem 2048 > /dev/null 2>&1
openssl req -new -key member-key.pem -out member.csr -subj "/CN=etcd-member" -config ${CONFIG} > /dev/null 2>&1
openssl x509 -req -in member.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out member.pem -days 365 -extensions ssl_client -extfile ${CONFIG} > /dev/null 2>&1

# Nodes and Admin
for i in node admin; do
    openssl genrsa -out ${i}-key.pem 2048 > /dev/null 2>&1
    openssl req -new -key ${i}-key.pem -out ${i}.csr -subj "/CN=kube-${i}" > /dev/null 2>&1
    openssl x509 -req -in ${i}.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out ${i}.pem -days 365 -extensions ssl_client  -extfile ${CONFIG} > /dev/null 2>&1
done

# Install certs
mv *.pem ${SSLDIR}/
