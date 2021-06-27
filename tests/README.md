# Kubespray cloud deployment tests

## Amazon Web Service

|              | Calico        | Flannel       | Weave         |
------------- | ------------- | ------------- | ------------- |
Debian Jessie | [![Build Status](https://ci.kubespray.io/job/kubespray-aws-calico-jessie/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-calico-jessie)  | [![Build Status](https://ci.kubespray.io/job/kubespray-aws-flannel-jessie/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-flannel-jessie/) | [![Build Status](https://ci.kubespray.io/job/kubespray-aws-weave-jessie/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-weave-jessie/) |
Ubuntu Trusty |[![Build Status](https://ci.kubespray.io/job/kubespray-aws-calico-trusty/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-calico-trusty/)|[![Build Status](https://ci.kubespray.io/job/kubespray-aws-flannel-trusty/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-flannel-trusty/)|[![Build Status](https://ci.kubespray.io/job/kubespray-aws-weave-trusty/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-weave-trusty)|
RHEL 7.2      |[![Build Status](https://ci.kubespray.io/job/kubespray-aws-calico-rhel72/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-calico-rhel72/)|[![Build Status](https://ci.kubespray.io/job/kubespray-aws-flannel-rhel72/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-flannel-rhel72/)|[![Build Status](https://ci.kubespray.io/job/kubespray-aws-weave-rhel72/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-weave-rhel72/)|
CentOS 7      |[![Build Status](https://ci.kubespray.io/job/kubespray-aws-calico-centos7/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-calico-centos7/)|[![Build Status](https://ci.kubespray.io/job/kubespray-aws-flannel-centos7/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-flannel-centos7/)|[![Build Status](https://ci.kubespray.io/job/kubespray-aws-weave-centos7/badge/icon)](https://ci.kubespray.io/job/kubespray-aws-weave-centos7/)|

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
