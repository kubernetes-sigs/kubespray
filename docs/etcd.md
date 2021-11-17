# etcd

## Metrics

To expose metrics on a separate HTTP port, define it in the inventory with:

```yaml
etcd_metrics_port: 2381
```

To create a service `etcd-metrics` and associated endpoints in the `kube-system` namespace,
define it's labels in the inventory with:

```yaml
etcd_metrics_service_labels:
  k8s-app: etcd
  app.kubernetes.io/managed-by: Kubespray
  app: kube-prometheus-stack-kube-etcd
  release: prometheus-stack
```

The last two labels in the above example allows to scrape the metrics from the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart with the following Helm `values.yaml` :

```yaml
kubeEtcd:
  service:
    enabled: false
```
