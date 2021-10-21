# Prometheus Grafana

Kubespray 를 통해 Prometheus, Grafana 배포를 하기 위해서는 아래의 parameter 들을 설정해야 한다.
Prometheus, Grafana 설치를 위해 사용되는 이미지의 경로와 태그는 roles/kubernetes-apps/prometheus/defaults/main.yml 에 정의되어있다.

### Common
```yml
prometheus_namespace: "monitoring"
```

### Prometheus
```yml
prometheus_operator_image_repo: "image repo for prometheus operator container"
prometheus_operator_image_tag: "image tag for prometheus operator container"
config_reloader_image_repo: "image repo for config reloader container"
config_reloader_image_tag: "image tag for config reloader container"
configmap_reloader_image_repo: "image repo for configmap reloader container"
configmap_reloader_image_tag: "image repo for configmap reloader container"

alertmanager_image_repo: "image repo for alert manager container"
alertmanager_image_tag: "image tag for alert manager container"

node_exporter_image_repo: "image repo for node exporter container"
node_exporter_image_tag: "image tag for node exporter container"
kube_rbac_proxy_image_repo: "image repo for kube rbac proxy container"
kube_rbac_proxy_image_tag: "image tag for kube rbac proxy container"

prometheus_adapter_image_repo: "image repo for prometheus adapter container"
prometheus_adapter_image_tag: "image tag for prometheus adapter container"

prometheus_image_repo: "image repo for prometheus container"
prometheus_image_tag: "image tag for prometheus container"
prometheus_pvc: "prometheus pvc size"

kube_state_metrics_image_repo: "image repo for kube state metrics container"
kube_state_metrics_image_tag: "image tag for kube state metrics container"
master_ip: "address of master node"

```

## Grafana Keycloak 연동
* 목적 : 'Keycloak 연동'
* 순서: 
	* keycloak에서 client 생성 후
	* Client protocol = openid-connect , Access type = confidential Standard Flow Enabled = On, Direct Access Grants Enabled = On
	* Root URL = https://${DOMAIN}/api/grafana/, Valid Redirect URIs = https://${DOMAIN}/api/grafana/login/generic_oauth/* , Admin URL = https://${DOMAIN}/api/grafana/, Web Origins = https://${DOMAIN}/api/grafana/
	* Client > grafana > Credentials > Secret 복사 후 https://github.com/tmax-cloud/kubespray/blob/tmax-master/roles/kubernetes-apps/prometheus/defaults/main.yml 에 client_secret와 client_id에 파라미터 값을 넣어준다.
	* domain = console의 주소
![image](https://user-images.githubusercontent.com/66110096/118447268-8a7f3000-b72b-11eb-9bdd-01d4252427c6.png)


### Grafana
```yml
grafana_home: "Grafana home"
grafana_image_repo: "image repo for grafana container"
grafana_image_tag: "image tag for grafana container"
domain: "hypercloud domain address"
client_id: "keycloak client id"
client_secret: "keycloak client secret"
keycloak_addr: "keycloak address"
grafana_pvc: "Grafana pvc size"
```


### 예시

```yml
prometheus_operator_image_repo: "quay.io/coreos/prometheus-operator"
prometheus_operator_image_tag: "v0.34.0"
config_reloader_image_repo: "quay.io/coreos/configmap-reload"
config_reloader_image_tag: "v0.0.1"
configmap_reloader_image_repo: "quay.io/coreos/prometheus-config-reloader"
configmap_reloader_image_tag: "v0.34.0"

alertmanager_image_repo: "quay.io/prometheus/alertmanager"
alertmanager_image_tag: "v0.20.0"

node_exporter_image_repo: "quay.io/prometheus/node-exporter"
node_exporter_image_tag: "v0.18.1"
kube_rbac_proxy_image_repo: "quay.io/coreos/kube-rbac-proxy"
kube_rbac_proxy_image_tag: "v0.4.1"

prometheus_adapter_image_repo: "quay.io/coreos/k8s-prometheus-adapter-amd64"
prometheus_adapter_image_tag: "v0.5.0"

prometheus_image_repo: "quay.io/prometheus/prometheus"
prometheus_image_tag: "v2.11.0"
prometheus_pvc: "10Gi"

kube_state_metrics_image_repo: "quay.io/coreos/kube-state-metrics"
kube_state_metrics_image_tag: "v1.8.0"
master_ip: "192.168.9.216"

```

### Grafana
```yml
grafana_home: "~/grafana-install"
grafana_image_repo: "grafana/grafana"
grafana_image_tag: "6.4.3"
domain: "192.168.9.156"
client_id: "grafana"
client_secret: "514512a6-b562-4058-9cb0-ce3faefb9e81"
keycloak_addr: "hyperauth.org"
grafana_pvc: "10Gi"
```

