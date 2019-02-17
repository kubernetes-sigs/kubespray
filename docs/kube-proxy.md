Kube-proxy
===========

The Kubernetes network proxy runs on each node. This reflects services as defined in the Kubernetes API on
each node and can do simple TCP, UDP, and SCTP stream forwarding or round robin TCP, UDP, and SCTP forwarding
across a set of backends.

## Kube-proxy install as static pod when non-kubeadm installation

Default values in role kubernetes/node

## Kubeadm install kube-proxy as DaemonSet

Default values in role kubernetes/master
