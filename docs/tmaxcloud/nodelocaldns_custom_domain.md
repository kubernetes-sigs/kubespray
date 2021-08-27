# NodeLocalDNS custom domain 설정  

* Local `nip.io` 도메인 추가를 위한 설정입니다.  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```yaml
  enable_local_nip_domain: true
  ```

* Ingress host 도메인용으로 custom 도메인 추가를 위한 설정입니다.  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```yaml
  enable_custom_domain: true
  custom_domain_name: "hypercloud.shinhan.com"
  custom_domain_ip: 10.12.10.12
  ```
  사용 예시:  `{{호스트}}.hypercloud.shinhan.com` DNS query할 때 응답은 10.12.10.12 

* Update kube-apiserver POD's dnsPolicy to 'clusterFirstWithNet'
  ```yaml
   api_server_dns_cfwhn: true
  ```
