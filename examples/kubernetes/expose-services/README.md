Examples how to expose k8s services
===================================

Exposing dashboard via frontend and externalIPs
-----------------------------------------------

* Edit `kubernetes-dashboard.yaml` and update `externalIPs` to the list of external IPs of your k8s minions

* Run:

```bash
kubectl create -f kubernetes-dashboard.yaml --namespace=kube-system
```

* Access:

```bash
curl $ANY_MINION_EXTERNAL_IP:9090
```

Exposing dashboard via nodePort
-------------------------------

* Get nodePort of the service:

```bash
echo $(kubectl --namespace=kube-system get svc/kubernetes-dashboard -o go-template='{{(index .spec.ports 0).nodePort}}')
```

* NAT on your router/jump-box to any k8s minion public IP and nodePort to provide external access:

```bash
iptables -t nat -I PREROUTING -p tcp --dport 9090 -j DNAT --to-destination 10.210.0.12:32005
iptables -t nat -I POSTROUTING -d 10.210.0.12 ! -s 10.210.0.0/24 -j MASQUERADE
iptables -I FORWARD -d 10.210.0.12 -j ACCEPT
```

Where `10.210.0.12` is public IP of one of your k8s minions and `32005` is nodePort of `kubernetes-dashboard` service.

* Access:

```bash
curl 10.210.0.12:9090
```

