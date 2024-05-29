# CentOS and derivatives

## CentOS 8

If you have containers that are using iptables in the host network namespace (`hostNetwork=true`),
you need to ensure they are using iptables-nft.
An example how k8s do the autodetection can be found [in this PR](https://github.com/kubernetes/kubernetes/pull/82966)
