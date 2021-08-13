# Helm Operator

kubespray로 helm operator 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
helm_operator_namespace: helm operator가 설치 될 네임스페이스
helm_operator_image: helm operator 이미지
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
helm_operator_namespace: "helm-system"
helm_operator_image: "docker.io/fluxcd/helm-operator:1.2.0"
```
