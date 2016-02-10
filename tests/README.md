# k8s-integration-tests

*Work In Progress*

## Test environment variables

### Common

Variable              | Description                            | Required   | Default
--------------------- | -------------------------------------- | ---------- | --------
`TEST_ID`             | A unique execution ID for this test    | Yes        |
`KUBE_NETWORK_PLUGIN` | The network plugin (calico or flannel) | Yes        |
`PRIVATE_KEY_FILE`    | The path to the SSH private key file   | No         |

### AWS Tests

Variable              | Description                                     | Required   | Default
--------------------- | ----------------------------------------------- | ---------- | ---------
`AWS_ACCESS_KEY`      | The Amazon Access Key ID                        | Yes        |
`AWS_SECRET_KEY`      | The Amazon Secret Access Key                    | Yes        |
`AWS_AMI_ID`          | The AMI ID to deploy                            | Yes        |
`AWS_KEY_PAIR_NAME`   | The name of the EC2 key pair to use             | Yes        |
`AWS_SECURITY_GROUP`  | The EC2 Security Group to use                   | No         | default
`AWS_REGION`          | The EC2 region                                  | No         | eu-central-1

#### Use private ssh key

##### Key

```bash
openssl pkcs12 -in gce-secure.p12 -passin pass:notasecret -nodes -nocerts | openssl rsa -out gce-secure.pem
cat gce-secure.pem |base64 -w0 > GCE_PEM_FILE`
```
