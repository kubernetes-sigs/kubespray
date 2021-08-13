#!/usr/bin/env bash

# Script to be used for generating testing certs only for notary-server and notary-signer
# Will also create a root-ca and intermediate-ca, deleting those keys when finished

PLATFORM=$(awk -F= '/^NAME/{print $2}' /etc/os-release)

OPENSSLCNF=""

if [[ "$PLATFORM" = *"Ubuntu"* ]]; then
        echo "Platform is Ubuntu"
        OPENSSLCNF=
        for path in /etc/openssl/openssl.cnf /etc/ssl/openssl.cnf /usr/local/etc/openssl/openssl.cnf; do
           if [[ -e ${path} ]]; then
               OPENSSLCNF=${path}
           fi
        done
elif [[ "$PLATFORM" = *"CentOS"* ]] || [[ "$PLATFORM" = *"ProLinux"* ]] || [[ "$PLATFORM" = *"Red Hat Enterprise Linux Server"* ]]; then
        echo "Platform is CentOS or ProLinux"
        echo "CentOS version must be 7.x or 8.x"
        OPENSSLCNF=
        for path in /etc/pki/tls/openssl.cnf; do
           if [[ -e ${path} ]]; then
               OPENSSLCNF=${path}
           fi
        done
else
        echo "Unknown Platform: $Platform"
fi


if [[ -z ${OPENSSLCNF} ]]; then
    printf "Could not find openssl.cnf"
    exit 1
fi

# First generates root-ca
openssl genrsa -out "hypercloud-root-ca.key" 4096
openssl req -new -key "hypercloud-root-ca.key" -out "hypercloud-root-ca.csr" -sha256 \
        -subj '/C=KR/ST=CA/L=San Francisco/O=Tmax/CN=Tmax CA'

cat > "hypercloud-root-ca.cnf" <<EOL
[root_ca]
basicConstraints = critical,CA:TRUE,pathlen:1
keyUsage = critical, nonRepudiation, cRLSign, keyCertSign
subjectKeyIdentifier=hash
EOL

openssl x509 -req -days 3650 -in "hypercloud-root-ca.csr" -signkey "hypercloud-root-ca.key" -sha256 \
        -out "hypercloud-root-ca.crt" -extfile "hypercloud-root-ca.cnf" -extensions root_ca

rm "hypercloud-root-ca.cnf" "hypercloud-root-ca.csr"

for i in "$@"
do
case $i in
    -ip=*)
    if [[ -z "$subjectAltName" ]]; then
        subjectAltName="subjectAltName = IP:${i#*=}"
    else
        subjectAltName="${subjectAltName}, IP:${i#*=}"
    fi
    shift # past argument=value
    ;;
    -dns=*)
    if [[ -z "$subjectAltName" ]]; then
        subjectAltName="subjectAltName = DNS:${i#*=}"
    else
        subjectAltName="${subjectAltName}, DNS:${i#*=}"
    fi
    shift # past argument=value
    ;;
esac
done


###
NEW_CRT_NAME=hyperauth
openssl genrsa -out "${NEW_CRT_NAME}.key" 4096
openssl req -new -key "${NEW_CRT_NAME}.key" -out "${NEW_CRT_NAME}.csr" -sha256 \
        -subj "/C=KR/ST=CA/L=San Francisco/O=Tmax/CN=${NEW_CRT_NAME}"

cat > "${NEW_CRT_NAME}.cnf" <<EOL
[${NEW_CRT_NAME}]
authorityKeyIdentifier=keyid,issuer
basicConstraints = critical,CA:FALSE
extendedKeyUsage=serverAuth,clientAuth
keyUsage = critical, digitalSignature, keyEncipherment
${subjectAltName}
subjectKeyIdentifier=hash
EOL

openssl x509 -req -days 750 -in "${NEW_CRT_NAME}.csr" -sha256 \
        -CA "hypercloud-root-ca.crt" -CAkey "hypercloud-root-ca.key"  -CAcreateserial \
        -out "${NEW_CRT_NAME}.crt" -extfile "${NEW_CRT_NAME}.cnf" -extensions ${NEW_CRT_NAME}
# append the intermediate cert to this one to make it a proper bundle

rm "${NEW_CRT_NAME}.cnf" "${NEW_CRT_NAME}.csr"
rm hypercloud-root-ca.srl
