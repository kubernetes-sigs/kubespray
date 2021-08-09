# Service Mesh

kubespray로 service mesh 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
service_mesh_namespace: service mesh 설치 네임스페이스
service_mesh_istio_image: istio 이미지
service_mesh_proxyv2_image: envoy proxy 이미지
service_mesh_jaeger_image: jaeger 이미지
service_mesh_kiali_image: kiali 이미지
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
service_mesh_namespace: "istio-system"
service_mesh_istio_image: "docker.io/istio/pilot:1.5.1"
service_mesh_proxyv2_image: "docker.io/istio/proxyv2:1.5.1"
service_mesh_jaeger_image: "docker.io/jaegertracing/all-in-one:1.16"
service_mesh_kiali_image: "quay.io/kiali/kiali:v1.21"
```
