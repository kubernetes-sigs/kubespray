# default_storageclass

kubespray로 default_storageclass 설정 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야 하는 값은 다음과 같습니다.

```yml
default_storageclass_name: default storageclass로 사용할 storageclass의 이름
```

- `default_storageclass_name`은 hypercloud를 통해 설치되는 storageclass (nfs나 efs-sc)여도 되고 사용자가 직접 설치한 storageclass 여도 됩니다.


### 예시

예를 들어 아래와 같이 변수들의 값을 설정합니다.

```yml
default_storageclass_name: nfs
```
