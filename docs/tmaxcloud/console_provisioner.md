# console_provisioner

kubespray로 console_provisioner 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
nfs_namespace: nfs provisioner pod을 배포 할 namespace의 이름
nfs_server: nfs server의 ip 주소
nfs_path: nfs server에서 외부로 공유 할 디렉토리

console_ver: console의 이미지 버전 
realm: hyperauth에 설정된 realm  
keycloak: hyperauth domain 주소 
clientid: hyperauth의 client id 
mc_mode: multicluster UI 설정 
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```bash
---
## Console Version
console_ver: "5.0.22.0"
# hyperauth(keycloak)에서 설정한 REALM정보 입력
realm: "tmax"
# hyperauth ip 주소 혹은 도메인 주소 입력 (같은 클러스터 내에 존재한다면, kubectl get svc -n hyperauth hyperauth로 조회가능)
keycloak: "hyperauth.org"
# hyperauth(keycloak)에서 설정하 Client Id 정보 입력
clientid: "hypercloud5"
# Multi Cluster 모드로 설치하려는 경우 true 입력 (Single Cluster 모드이 경우 false)
mc_mode: "true"

```