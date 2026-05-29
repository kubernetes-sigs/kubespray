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

The last two labels in the above example allows to scrape the metrics from the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart when it is installed with the release name `kube-prometheus-stack` and the following Helm `values.yaml`:

```yaml
kubeEtcd:
  service:
    enabled: false
```

If your Helm release name is different, adjust the `release` label accordingly.

To fully override metrics exposition URLs, define it in the inventory with:

```yaml
etcd_listen_metrics_urls: "http://0.0.0.0:2381"
```

If you choose to expose metrics on specific node IPs (for example `10.141.4.22`, `10.141.4.23`, `10.141.4.24`) in `etcd_listen_metrics_urls`,
you can configure kube-prometheus-stack to scrape those endpoints directly with:

```yaml
kubeEtcd:
  enabled: true
  endpoints:
    - 10.141.4.22
    - 10.141.4.23
    - 10.141.4.24
```
