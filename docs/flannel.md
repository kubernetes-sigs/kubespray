Flannel
==============

* Flannel configuration file should have been created there

```
cat /run/flannel/subnet.env
FLANNEL_NETWORK=10.233.0.0/18
FLANNEL_SUBNET=10.233.16.1/24
FLANNEL_MTU=1450
FLANNEL_IPMASQ=false
```

* Check if the network interface has been created

```
ip a show dev flannel.1
4: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN group default
    link/ether e2:f3:a7:0f:bf:cb brd ff:ff:ff:ff:ff:ff
    inet 10.233.16.0/18 scope global flannel.1
       valid_lft forever preferred_lft forever
    inet6 fe80::e0f3:a7ff:fe0f:bfcb/64 scope link
       valid_lft forever preferred_lft forever
```

* Try to run a container and check its ip address

```
kubectl run test --image=busybox --command -- tail -f /dev/null
replicationcontroller "test" created

kubectl describe po test-34ozs | grep ^IP
IP:                             10.233.16.2
```

```
kubectl exec test-34ozs -- ip a show dev eth0
8: eth0@if9: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1450 qdisc noqueue
    link/ether 02:42:0a:e9:2b:03 brd ff:ff:ff:ff:ff:ff
    inet 10.233.16.2/24 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:aff:fee9:2b03/64 scope link tentative flags 08
       valid_lft forever preferred_lft forever
```
