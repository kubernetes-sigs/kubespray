# nfs_external_provisioner

kubespray로 nfs_external_provisioner 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
nfs_namespace: nfs provisioner pod을 배포 할 namespace의 이름
nfs_server: nfs server의 ip 주소
nfs_path: nfs server에서 외부로 공유 할 디렉토리
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```bash
---
# defaults file for nfs_external_provisioner
nfs_external_provisioner_enabled: true
# replace with namespace where provisioner will be deployed
nfs_namespace: nfs
# replace with your nfs server
nfs_server: 192.168.7.17
# replace with your nfs exported path
nfs_path: /root/test

```

