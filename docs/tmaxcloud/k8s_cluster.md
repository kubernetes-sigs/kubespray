# k8s_cluster 환경 설정

kubespray 설치를 위해 inventory/tmaxcloud/group_vars/group_vars/k8s_cluster/k8s-cluster.yml 을 수정한다.

```yml
kube_version: k8s version

kube_network_plugin: cni 설정

kube_service_addresses: service pod 대역 설정

kube_pods_subnet: pod 네트워크 대역 설정

kube_proxy_mode: proxy mode configuration

enable_nodelocaldns: node local dns 사용 설정
nodelocaldns_ip: node local dns ip
nodelocaldns_health_port: node local dns port

enable_local_nip_domain: local nip 사용 여부 (사용시 true)
enable_custom_domain: custum domain 사용 여부 (사용시 true)
custom_domain_name: custum domain name
custom_domain_ip: custum domain ip

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

enable_nodelocaldns: true
nodelocaldns_ip: 169.254.25.10
nodelocaldns_health_port: 9254

enable_local_nip_domain: true
enable_custom_domain: true
custom_domain_name: "hypercloud.shinhan.com"
custom_domain_ip: "192.168.9.174"

container_manager: crio
```
