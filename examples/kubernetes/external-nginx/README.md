Nginx example with external IPs
===============================

* Edit `nginx-frontend.yaml` and update `externalIPs` to the list of external IPs of your k8s minions

* Deploy:

```bash
kubectl create -f nginx-backends.yaml
kubectl create -f nginx-frontend.yaml
```

* Check:

```bash
curl $ANY_MINION_EXTERNAL_IP
```

