# NodeLocalDNS - Local nip.io domain 설정
kubespray로 nodelocaldns 설치하고 Local `nip.io` 도메일 추가를 위한 설정입니다.  

파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
```yaml
enable_local_nip_domain: true
```
