# CentOS and derivatives

## CentOS 7

The maximum python version officially supported in CentOS is 3.6. Ansible as of version 5 (ansible core 2.12.x) increased their python requirement to python 3.8 and above.
Kubespray supports multiple ansible versions but only the default (5.x) gets wide testing coverage. If your deployment host is CentOS 7 it is recommended to use one of the earlier versions still supported.

## CentOS 8

If you have containers that are using iptables in the host network namespace (`hostNetwork=true`),
you need to ensure they are using iptables-nft.
An example how k8s do the autodetection can be found [in this PR](https://github.com/kubernetes/kubernetes/pull/82966)
