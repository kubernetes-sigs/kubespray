# all 환경 설정

offline 환경에서의 kubespray 설치를 위해 inventory/tmaxcloud/group_vars/all/all.yml 을 수정한다.

```yml
apiserver_loadbalancer_domain_name: "{{controlplain VIP}}"
loadbalancer_apiserver:
  address: {{controlplain VIP}}
  port: 6443
  
upstream_dns_servers:
  - {{upstream dns ip}}  
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
apiserver_loadbalancer_domain_name: "10.0.10.50"
loadbalancer_apiserver:
  address: 10.0.10.50
  port: 6443
  
upstream_dns_servers:
  - 192.168.1.150  
```
