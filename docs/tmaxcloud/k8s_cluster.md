# k8s_cluster 환경 설정

kubespray 설치를 위해 inventory/tmaxcloud/group_vars/group_vars/k8s_cluster/k8s-cluster.yml 을 수정한다.

```yml
kube_version: k8s version

kube_network_plugin: cni 설정

kube_service_addresses: service pod 대역 설정

kube_pods_subnet: pod 네트워크 대역 설정

kube_proxy_mode: proxy mode configuration

container_manager: container runtime 설정
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
kube_version: v1.19.4

kube_network_plugin: calico

kube_service_addresses: 10.96.0.0/16

kube_pods_subnet: 10.244.0.0/16

kube_proxy_mode: iptables

dns_mode: coredns

container_manager: crio
```
