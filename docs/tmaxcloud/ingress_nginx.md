# Ingress Nginx

kubespray로 nginx ingress controller 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
ingress_nginx_name: 설치 네임스페이스 및 ingress controller 관련 리소스들의 이름
ingress_nginx_controller_image: nginx ingress controller 이미지
ingress_nginx_certgen_image: 인증서 생성을 위한 certgen 이미지
ingress_nginx_class: ingress controller 구동 시 설정 할 ingress class
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
ingress_nginx_name: "ingress-nginx"
ingress_nginx_controller_image: "quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.33.0"
ingress_nginx_certgen_image: "docker.io/jettech/kube-webhook-certgen:v1.2.2"
ingress_nginx_class: "ingress-nginx"
```
