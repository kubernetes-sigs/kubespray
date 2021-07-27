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

## ip-masq-agent with Cilium

If you are using masquerade: "true" and enable-bpf-masquerade: "true" together
with tunnel: "vxlan" or "geneve"
By default, any packet from a pod destined to an IP address outside of
POD cidr range is masqueraded. To allow more fine-grained
control, Cilium implements ip-masq-agent in eBPF which can be enabled
setting "enable_ip_masq_agent" to true, this will add the necessary
ConfigMap mounts to Cilium DS as optional and you will have to enable it with:

```yml
enable_ip_masq_agent: true
```

this will add optional volumeMounts to Cilium DaemonSet for it. Cilium will add he following CIDR as non masquerading destinations:

```yml
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
100.64.0.0/10
192.0.0.0/24
192.0.2.0/24
192.88.99.0/24
198.18.0.0/15
198.51.100.0/24
203.0.113.0/24
240.0.0.0/4
```

If you want to control this CIDR destinations you can do so by creating additional ConfigMap in kube-system namespace named `ip-mask-agent`:

```yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ip-masq-agent
  namespace: kube-system
data:
  config: |-
    nonMasqueradeCIDRs:
      - 10.0.0.1/32
      - 172.16.0.0/12
    masqLinkLocal: false
    masqLinkLocalIPv6: false
    resyncInterval: 60s
```

more information about ip-masq-agent can be found in the  [official docs](https://docs.cilium.io/en/stable/concepts/networking/masquerading/)
