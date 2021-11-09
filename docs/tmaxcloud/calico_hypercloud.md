# Calico

kubespray로 Calico 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/k8s-net-calico.yml에서 설정해야하는 값은 다음 하나의 값이다.

```yml
calico_ip_auto_method: "cidr=HOST-POD-NETWORK-SUBNET/CIDR"
```

HOST-POD-NETWORK-SUBNET/CIDR 값은 설치하는 클러스터에서 파드 통신을 위해 사용하는 네트워크의 주소를 CIDR 형식으로 나타낸 것이다.

### 예시

예를 들어 다음과 같이 확인 가능하다.

```bash
$ ip addr show dev enp3s0
3: enp3s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 94:de:80:0e:2f:ea brd ff:ff:ff:ff:ff:ff
    inet 192.168.7.93/24 brd 192.168.7.255 scope global enp3s0
       valid_lft forever preferred_lft forever
    inet6 fe80::96de:80ff:fe0e:2fea/64 scope link
       valid_lft forever preferred_lft forever
```

파드 네트워크에 해당하는 인터페이스의 ip 주소로부터 네트워크의 네트워크주소 확인 → 192.168.7.0/24

```yml
calico_ip_auto_method: "cidr=192.168.7.0/24"
```

### AWS 환경에서 IP-in-IP 모드 사용을 위한 설정입니다.
파일: inventory/tmaxcloud/group_vars/k8s_cluster/k8s-net-calico.yml
```yml
calico_ipip_mode: 'Always'
```
