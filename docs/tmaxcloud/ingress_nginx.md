# Ingress Nginx

kubespray로 nginx ingress controller 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
ingress_nginx_service_type: nginx ingress controller의 서비스 타입
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
ingress_nginx_service_type: NodePort
```
