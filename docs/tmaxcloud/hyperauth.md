# Hyperauth

kubespray로 Hyperauth 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같다.

```yml
hyperauth_enabled: hyperauth 설치 여부 (true/false)
hyperauth_version: hyperauth 서버 버전
```


### 예시
```yml
hyperauth_enabled: true
hyperauth_version: "latest"
```

