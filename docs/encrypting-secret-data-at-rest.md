# Encrypting Secret Data at Rest

Before enabling Encrypting Secret Data at Rest, please read the following documentation carefully.

<https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/>

As you can see from the documentation above, 5 encryption providers are supported as of today (22.02.2022).

As default value for the provider we have chosen `secretbox`.

Alternatively you can use the values `identity`, `aesgcm`, `aescbc` or `kms`.

| Provider | Why we have decided against the value as default                                                                                                                                         |
|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| identity | no encryption                                                                                                                                                                            |
| aesgcm   | Must be rotated every 200k writes                                                                                                                                                        |
| aescbc   | Not recommended due to CBC's vulnerability to padding oracle attacks.                                                                                                                    |
| kms      | Is the official recommended way, but assumes that a key management service independent of Kubernetes exists, we cannot assume this in all environments, so not a suitable default value. |

## Details about Secretbox

Secretbox uses [Poly1305](https://cr.yp.to/mac.html) as message-authentication code and [XSalsa20](https://www.xsalsa20.com/) as secret-key authenticated encryption and secret-key encryption.
