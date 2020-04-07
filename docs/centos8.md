# RHEL / CentOS 8

RHEL / CentOS 8 ships only with iptables-nft (ie without iptables-legacy)
The only tested configuration for now is using Calico CNI
You need to use K8S 1.17+ and to add `calico_iptables_backend: "NFT"` to your configuration

If you have containers that are using iptables in the host network namespace (`hostNetwork=true`),
you need to ensure they are using iptables-nft.
An exemple how k8s do the autodetection can be found [in this PR](https://github.com/kubernetes/kubernetes/pull/82966)
