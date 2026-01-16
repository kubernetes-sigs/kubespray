# Installation Guide

- [Installation Guide](#installation-guide)
  - [Kubernetes TLS Root CA Certificate/Key Secret](#kubernetes-tls-root-ca-certificatekey-secret)
  - [Securing Ingress Resources](#securing-ingress-resources)
    - [Create New TLS Root CA Certificate and Key](#create-new-tls-root-ca-certificate-and-key)
      - [Install Cloudflare PKI/TLS `cfssl` Toolkit.](#install-cloudflare-pkitls-cfssl-toolkit)
      - [Create Root Certificate Authority (CA) Configuration File](#create-root-certificate-authority-ca-configuration-file)
      - [Create Certficate Signing Request (CSR) Configuration File](#create-certficate-signing-request-csr-configuration-file)
      - [Create TLS Root CA Certificate and Key](#create-tls-root-ca-certificate-and-key)

Cert-Manager is a native Kubernetes certificate management controller. It can help with issuing certificates from a variety of sources, such as Let’s Encrypt, HashiCorp Vault, Venafi, a simple signing key pair, or self signed. It will ensure certificates are valid and up to date, and attempt to renew certificates at a configured time before expiry.

## Kubernetes TLS Root CA Certificate/Key Secret

If you're planning to secure your ingress resources using TLS client certificates, you'll need to create and deploy the Kubernetes `ca-key-pair` secret consisting of the Root CA certificate and key to your K8s cluster.

For further information, read the official [Cert-Manager CA Configuration](https://cert-manager.io/docs/configuration/ca/) doc.

`cert-manager` can now be enabled by editing your K8s cluster addons inventory e.g. `inventory\sample\group_vars\k8s_cluster\addons.yml` and setting `cert_manager_enabled` to true.

```ini
# Cert manager deployment
cert_manager_enabled: true
```

If you don't have a TLS Root CA certificate and key available, you can create these by following the steps outlined in section [Create New TLS Root CA Certificate and Key](#create-new-tls-root-ca-certificate-and-key) using the Cloudflare PKI/TLS `cfssl` toolkit. TLS Root CA certificates and keys can also be created using `ssh-keygen` and OpenSSL, if `cfssl` is not available.

## Securing Ingress Resources

A common use-case for cert-manager is requesting TLS signed certificates to secure your ingress resources. This can be done by simply adding annotations to your Ingress resources and cert-manager will facilitate creating the Certificate resource for you. A small sub-component of cert-manager, ingress-shim, is responsible for this.

To enable the Nginx Ingress controller as part of your Kubespray deployment, simply edit your K8s cluster addons inventory e.g. `inventory\sample\group_vars\k8s_cluster\addons.yml` and set `ingress_nginx_enabled` to true.

```ini
# Nginx ingress controller deployment
ingress_nginx_enabled: true
```

For example, if you're using the Nginx ingress controller, you can secure the Prometheus ingress by adding the annotation `cert-manager.io/cluster-issuer: ca-issuer` and the `spec.tls` section to the `Ingress` resource definition.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prometheus-k8s
  namespace: monitoring
  labels:
    prometheus: k8s
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: ca-issuer
spec:
  tls:
  - hosts:
    - prometheus.example.com
    secretName: prometheus-dashboard-certs
  rules:
  - host: prometheus.example.com
    http:
      paths:
      - path: /
        pathType: ImplementationSpecific
        backend:
          service:
            name: prometheus-k8s
            port:
              name: web
```

Once deployed to your K8s cluster, every 3 months cert-manager will automatically rotate the Prometheus `prometheus.example.com` TLS client certificate and key, and store these as the Kubernetes `prometheus-dashboard-certs` secret.

Please consult the official upstream documentation:

- [cert-manager Ingress Usage](https://cert-manager.io/v1.5-docs/usage/ingress/)
- [cert-manager Ingress Tutorial](https://cert-manager.io/v1.5-docs/tutorials/acme/ingress/#step-3-assign-a-dns-name)

### ACME

The ACME Issuer type represents a single account registered with the Automated Certificate Management Environment (ACME) Certificate Authority server. When you create a new ACME Issuer, cert-manager will generate a private key which is used to identify you with the ACME server.

Certificates issued by public ACME servers are typically trusted by client’s computers by default. This means that, for example, visiting a website that is backed by an ACME certificate issued for that URL, will be trusted by default by most client’s web browsers. ACME certificates are typically free.

- [ACME Configuration](https://cert-manager.io/v1.5-docs/configuration/acme/)
- [ACME HTTP Validation](https://cert-manager.io/v1.5-docs/tutorials/acme/http-validation/)
  - [HTTP01 Challenges](https://cert-manager.io/v1.5-docs/configuration/acme/http01/)
- [ACME DNS Validation](https://cert-manager.io/v1.5-docs/tutorials/acme/dns-validation/)
  - [DNS01 Challenges](https://cert-manager.io/v1.5-docs/configuration/acme/dns01/)
- [ACME FAQ](https://cert-manager.io/v1.5-docs/faq/acme/)

#### ACME With An Internal Certificate Authority

The ACME Issuer with an internal certificate authority requires cert-manager to trust the certificate authority. This trust must be done at the cert-manager deployment level.
To add a trusted certificate authority to cert-manager, add it's certificate to `group_vars/k8s-cluster/addons.yml`:

```yaml
cert_manager_trusted_internal_ca: |
  -----BEGIN CERTIFICATE-----
  [REPLACE with your CA certificate]
  -----END CERTIFICATE-----
```

Once the CA is trusted, you can define your issuer normally.

### Create New TLS Root CA Certificate and Key

#### Install Cloudflare PKI/TLS `cfssl` Toolkit

e.g. For Ubuntu/Debian distributions, the toolkit is part of the `golang-cfssl` package.

```shell
sudo apt-get install -y golang-cfssl
```

#### Create Root Certificate Authority (CA) Configuration File

The default TLS certificate expiry time period is `8760h` which is 1 years from the date the certificate is created.

```shell
$ cat > ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "kubernetes": {
        "usages": ["signing", "key encipherment", "server auth", "client auth"],
        "expiry": "8760h"
      }
    }
  }
}
EOF
```

#### Create Certficate Signing Request (CSR) Configuration File

The TLS certificate `names` details can be updated to your own specific requirements.

```shell
$ cat > ca-csr.json <<EOF
{
  "CN": "Kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "Kubernetes",
      "OU": "CA",
      "ST": "Oregon"
    }
  ]
}
EOF
```

#### Create TLS Root CA Certificate and Key

```shell
$ cfssl gencert -initca ca-csr.json | cfssljson -bare ca
ca.pem
ca-key.pem
```

Check the TLS Root CA certificate has the correct `Not Before` and `Not After` dates, and ensure it is indeed a valid Certificate Authority with the X509v3 extension `CA:TRUE`.

```shell
$ openssl x509 -text -noout -in ca.pem

Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            6a:d4:d8:48:7f:98:4f:54:68:9a:e1:73:02:fa:d0:41:79:25:08:49
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C = US, ST = Oregon, L = Portland, O = Kubernetes, OU = CA, CN = Kubernetes
        Validity
            Not Before: Jul 10 15:21:00 2020 GMT
            Not After : Jul  9 15:21:00 2025 GMT
        Subject: C = US, ST = Oregon, L = Portland, O = Kubernetes, OU = CA, CN = Kubernetes
        Subject Public Key Info:
        ...
        X509v3 extensions:
            X509v3 Key Usage: critical
                Certificate Sign, CRL Sign
            X509v3 Basic Constraints: critical
                CA:TRUE
            X509v3 Subject Key Identifier:
                D4:38:B5:E2:26:49:5E:0D:E3:DC:D9:70:73:3B:C4:19:6A:43:4A:F2
                ...
```
