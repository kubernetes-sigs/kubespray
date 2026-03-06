# etcd

## Deployment Types

It is possible to deploy etcd with three methods. To change the default deployment method (host), use the `etcd_deployment_type` variable. Possible values are `host`, `kubeadm`, and `docker`.

### Host

Host deployment is the default method. Using this method will result in etcd installed as a systemd service.

### Docker

Installs docker in etcd group members and runs etcd on docker containers. Only usable when `container_manager` is set to `docker`.

### Kubeadm

This deployment method is experimental and is only available for new deployments. This deploys etcd as a static pod on control plane hosts.

## Metrics

To expose metrics on a separate HTTP port, define it in the inventory with:

```yaml
etcd_metrics_port: 2381
```

To create a service `etcd-metrics` and associated endpoints in the `kube-system` namespace,
define its labels in the inventory with:

```yaml
etcd_metrics_service_labels:
  k8s-app: etcd
  app.kubernetes.io/managed-by: Kubespray
  app: kube-prometheus-stack-kube-etcd
  release: kube-prometheus-stack
```

The last two labels in the above example allow scraping the metrics from the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart with the following Helm `values.yaml`:

```yaml
kubeEtcd:
  service:
    enabled: false
```

Make sure the `release` label matches the Helm release name of your
`kube-prometheus-stack` installation. The example above assumes the chart was
installed with the release name `kube-prometheus-stack`.

For host-based etcd deployments, you can also configure
`kube-prometheus-stack` with the etcd node IPs directly instead of relying on
label-based discovery:

```yaml
kubeEtcd:
  enabled: true
  endpoints:
    - 10.141.4.22
    - 10.141.4.23
    - 10.141.4.24
```

Those IPs should match the host deployment listen URLs exposed through
`/etc/etcd.env`.

To fully override metrics exposition urls, define it in the inventory with:

```yaml
etcd_listen_metrics_urls: "http://0.0.0.0:2381"
```
