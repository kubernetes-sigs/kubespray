# NodeLocalDNS custom domain 설정  
## Upstream DNS
  Upstream DNS는 CoreDNS가 관리하는 cluster domain에 질의한 도메인을 못 찾는 경우에 Upstream DNS로 forward해서 질의합니다.  

* Upstream DNS (forward DNS) 사용을 위한 설정입니다.  
  파일: `inventory/tmaxcloud/group_vars/all/all.yml`
  ```
  upstream_dns_servers:
    - 8.8.8.8
    - 8.8.4.4
  ```
  사용하고 싶지 않으면 
  ```
  #upstream_dns_servers:
  #  - 8.8.8.8
  #  - 8.8.4.4
  ```

## NodeLocal DNS
Nodelocal DNS는 Kubernetes의 DaedomSet로 만들어서 cache DNS서버로 사용합니다.  
Client POD들이 CoreDNS 서버한테 바로 갈 필요없고 같은 노드에 떠 있는 nodelocaldns 서버한테 먼저 물어보고 대답 없으면 nodelocaldns가 CoreDNS한테 query를 forward해주는 것입니다.  
전에 질의했던 query의 대답 결과는 cache로 저장돼어 있으니까 성능과 속도 빨라서 많이 사용합니다.  

* nodelocal DNS 사용을 위한 설정입니다.  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```
  enable_nodelocaldns: true
  nodelocaldns_ip: 169.254.25.10
  nodelocaldns_health_port: 9254
  ```
  `true` : nodelocaldns 사용, `false` nodelocaldns 미사용  
  `nodelocaldns_ip` : dummy interface를 만들어서 월하는 IP 사용  
   `nodelocaldns_health_port` : nodelocaldns의 health 체크 포트 번호


## Local Domain `nip.io`
외부 접속 안되는 환경에서 `nip.io` 도메인을 로컬에서 사용할 수 있게 만든 기능입니다.
* Local `nip.io` 도메인 추가를 위한 설정입니다.  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```yaml
  enable_local_nip_domain: true
  ```

## Custom Domain
`nip.io` 대신에 원하는 custom 도메인을 정해서 사용할 수 있게 만든 기능입니다.  
wildcard 도메인으로 만들어서 보통 Ingress hostname 도메인으로 많이 사용합니다.  
wildcard 도메인은 `*.my.domain  IN   A 1.2.3.4` 형식이라서 'my.domain' 도메인한테 질의할 때 모든 대답은 '1.2.3.4'입니다.
* Ingress host 도메인용으로 custom 도메인 추가를 위한 설정입니다.  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```yaml
  enable_custom_domain: true
  custom_domain_name: "hypercloud.shinhan.com"
  custom_domain_ip: 10.12.10.12
  ```
  사용 예시:  `{{호스트}}.hypercloud.shinhan.com` DNS query할 때 응답은 10.12.10.12 

## External CoreDNS - k8s_gatway
Kubernetes external resources (LoadBalancer Service, Ingress) 외부에서 도메인으로 접속 할 수 있게 해 주는 기능입니다.
* External CoreDNS 사용을 휘한 설정입니다.
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```yaml
  enable_excoredns: true
  excoredns_zone: "hypercloud.shinhan.com"
  ```
  `true` : External CoreDNS 사용, `false` External CoreDNS 미사용  
  `excoredns_zone`: 사용하고 싶은 도메인 이름 (ex: hypercloud.shinhan.com)  
  Service 사용 예시: {{ ServiceName }}.{{ ServiceNamespace }}.hypercloud.shinhan.com  
  Ingress 사용 예시: ingress의 FQDN hostname - spec.rules[].host  

## Static POD `kube-apiserver` 에 'clusterFirstWithHostNet' dnsPolicy 적용
기본적으로 kube-apiserver POD는 hostNetwork를 사용해서 cluster 네트워크랑 통신 안돼서 cluster domain 접속 안됩니다.  
cluster domain로 접속하려면 kube-apiserver POD에 cluster domain nameserver를 추가해줘야 합니다.  
그래서 kube-apiserver POD의 dnsPolicy는 'clusterFirstWithHostNet'로 바꿔야 합니다.
* Update kube-apiserver POD's dnsPolicy to 'clusterFirstWithHostNet'
  ```yaml
   api_server_dns_cfwhn: true
  ```
