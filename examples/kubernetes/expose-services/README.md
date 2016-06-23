Examples how to expose k8s services
===================================

* Edit `kubernetes-dashboard.yaml` and update `externalIPs` to the list of external IPs of your k8s minions

* Run:

```bash
kubectl create -f kubernetes-dashboard.yaml --namespace=kube-system
```

* Access:

```bash
curl $ANY_MINION_EXTERNAL_IP:9090
```

