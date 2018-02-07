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

      Environmental variables MASTERS and HOSTS should be set to generate keys
      for each host.

           ex :
           MASTERS=node1 HOSTS="node1 node2" $(basename $0) -f openssl.conf -d /srv/ssl
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
    SSLDIR="/etc/kubernetes/certs"
fi

tmpdir=$(mktemp -d /tmp/kubernetes_cacert.XXXXXX)
trap 'rm -rf "${tmpdir}"' EXIT
cd "${tmpdir}"

mkdir -p "${SSLDIR}"

# Root CA
if [ -e "$SSLDIR/ca-key.pem" ]; then
    # Reuse existing CA
    cp $SSLDIR/{ca.pem,ca-key.pem} .
else
    openssl genrsa -out ca-key.pem 2048 > /dev/null 2>&1
    openssl req -x509 -new -nodes -key ca-key.pem -days 10000 -out ca.pem -subj "/CN=kube-ca" > /dev/null 2>&1
fi

gen_key_and_cert() {
    local name=$1
    local subject=$2
    openssl genrsa -out ${name}-key.pem 2048 > /dev/null 2>&1
    openssl req -new -key ${name}-key.pem -out ${name}.csr -subj "${subject}" -config ${CONFIG} > /dev/null 2>&1
    openssl x509 -req -in ${name}.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out ${name}.pem -days 3650 -extensions v3_req -extfile ${CONFIG} > /dev/null 2>&1
}

# Admins
if [ -n "$MASTERS" ]; then
    # kube-apiserver
    # Generate only if we don't have existing ca and apiserver certs
    if ! [ -e "$SSLDIR/ca-key.pem" ] || ! [ -e "$SSLDIR/apiserver-key.pem" ]; then
      gen_key_and_cert "apiserver" "/CN=kube-apiserver"
      cat ca.pem >> apiserver.pem
    fi
    # If any host requires new certs, just regenerate scheduler and controller-manager master certs
    # kube-scheduler
    gen_key_and_cert "kube-scheduler" "/CN=system:kube-scheduler"
    # kube-controller-manager
    gen_key_and_cert "kube-controller-manager" "/CN=system:kube-controller-manager"
    # metrics aggregator
    gen_key_and_cert "front-proxy-client" "/CN=front-proxy-client"

    for host in $MASTERS; do
        cn="${host%%.*}"
        # admin
        gen_key_and_cert "admin-${host}" "/CN=kube-admin-${cn}/O=system:masters"
    done
fi

# Nodes
if [ -n "$HOSTS" ]; then
    for host in $HOSTS; do
        cn="${host%%.*}"
        gen_key_and_cert "node-${host}" "/CN=system:node:${cn,,}/O=system:nodes"
    done
fi

# system:node-proxier
if [ -n "$HOSTS" ]; then
    for host in $HOSTS; do
        # kube-proxy
        gen_key_and_cert "kube-proxy-${host}" "/CN=system:kube-proxy/O=system:node-proxier"
    done
fi

# Install certs
mv *.pem ${SSLDIR}/
