# Cilium

## Kube-proxy replacement with Cilium

Cilium can run without kube-proxy by setting `cilium_kube_proxy_replacement`
to `strict`.

Without kube-proxy, cilium needs to know the address of the kube-apiserver
and this must be set globally for all cilium components (agents and operators).
Hence, in this configuration in Kubespray, Cilium will always contact
the external loadbalancer (even from a node in the control plane)
and if there is no external load balancer It will ignore any local load
balancer deployed by Kubespray and **only contacts the first master**.
