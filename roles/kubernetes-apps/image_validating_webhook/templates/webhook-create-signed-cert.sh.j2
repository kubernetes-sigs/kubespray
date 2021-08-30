#!/bin/bash

# Generating ssl secret for webhook server

set -e

service=image-validation-admission-svc
secret=image-validation-admission-certs
namespace=registry-system

if [ ! -x "$(command -v openssl)" ]; then
    echo "openssl not found"
    exit 1
fi

csrName=${service}.${namespace}
tmpdir=$(mktemp -d)
echo "creating certs in tmpdir ${tmpdir} "

cat <<EOF >> "${tmpdir}"/csr.conf
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = ${service}
DNS.2 = ${service}.${namespace}
DNS.3 = ${service}.${namespace}.svc
EOF

openssl genrsa -out "${tmpdir}"/server-key.pem 2048
openssl req -new -key "${tmpdir}"/server-key.pem -subj "/CN=${service}.${namespace}.svc" -out "${tmpdir}"/server.csr -config "${tmpdir}"/csr.conf

# clean-up any previously created CSR for our service. Ignore errors if not present.
kubectl delete csr ${csrName} 2>/dev/null || true

# create  server cert/key CSR and  send to k8s API
cat <<EOF | kubectl create -f -
apiVersion: certificates.k8s.io/v1beta1
kind: CertificateSigningRequest
metadata:
  name: ${csrName}
spec:
  groups:
  - system:authenticated
  request: $(cat "${tmpdir}"/server.csr | base64 | tr -d '\n')
  usages:
  - digital signature
  - key encipherment
  - server auth
EOF

# verify CSR has been created
SECONDS=0
while true; do
  echo "... waiting for csr to be present in kubernetes"
  echo "kubectl get csr ${csrName}"
  kubectl get csr ${csrName} > /dev/null 2>&1
  if [ "$?" -eq 0 ]; then
      break
  fi
  if [[ $SECONDS -ge 60 ]]; then
    echo "[!] timed out waiting for csr"
    exit 1
  fi
  sleep 2
done

# approve and fetch the signed certificate
kubectl certificate approve ${csrName}
# verify certificate has been signed
for _ in $(seq 10); do
    serverCert=$(kubectl get csr ${csrName} -o jsonpath='{.status.certificate}')
    if [[ ${serverCert} != '' ]]; then
        break
    fi
    sleep 1
done
if [[ ${serverCert} == '' ]]; then
    echo "ERROR: After approving csr ${csrName}, the signed certificate did not appear on the resource. Giving up after 10 attempts." >&2
    exit 1
fi
echo "${serverCert}" | openssl base64 -d -A -out "${tmpdir}"/server-cert.pem


# create the secret with CA cert and server cert/key
kubectl create secret generic ${secret} \
        --from-file=key.pem="${tmpdir}"/server-key.pem \
        --from-file=cert.pem="${tmpdir}"/server-cert.pem \
        --dry-run -o yaml |
    kubectl -n ${namespace} apply -f -
