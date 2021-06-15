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

## Choose Cilium version

```yml
cilium_version: v1.8.9 ## or v1.9.6
```

## Add variable to config

Use following variables:

Example:

```yml
cilium_config_extra_vars:
  enable-endpoint-routes: true
```

## Install Cilium Hubble

k8s-net-cilium.yml:

```yml
cilium_enable_hubble: true ## enable support hubble in cilium
cilium_hubble_install: true ## install hubble-relay, hubble-ui
cilium_hubble_tls_generate: true ## install hubble-certgen and generate certificates
```

To validate that Hubble UI is properly configured, set up a port forwarding for hubble-ui service:

```shell script
kubectl port-forward -n kube-system svc/hubble-ui 12000:80
```

and then open [http://localhost:12000/](http://localhost:12000/).

## Hubble metrics

```yml
cilium_enable_hubble_metrics: true
cilium_hubble_metrics:
  - dns
  - drop
  - tcp
  - flow
  - icmp
  - http
```  

[More](https://docs.cilium.io/en/v1.9/operations/metrics/#hubble-exported-metrics)
