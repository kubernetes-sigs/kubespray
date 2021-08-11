# Federation

# Cluster API
  
kubespray로 Federation 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같다.

```yml
federation_enabled: Federation 설치 여부(true/false)
```


### 예시
```yml
federation_enabled: true
```

