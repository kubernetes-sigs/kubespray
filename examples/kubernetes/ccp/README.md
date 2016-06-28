CCP examples
============
Some examples for Openstack CCP.

Expose Horizon
==============

* Get nodePort of Horizon service:
```bash
echo $(kubectl --namespace=openstack get svc/horizon -o go-template='{{(index .spec.ports 0).nodePort}}')
```

* NAT on your router/jump-box to any k8s minion public IP and nodePort to provide external access:
```bash
iptables -t nat -I PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.210.0.12:32643
```

Where `10.210.0.12` is IP of one of your k8s minions and `32643` is nodePort of Horizon service.
