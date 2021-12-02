# EFK

Kubespray 를 통해 EFK 배포를 하기 위해서는 roles/kubernetes-apps/efk/defaults/main.yml 아래의 parameter 들을 설정해야 한다.

### Common
```yml
efk_namespace: "namespace for EFK stack"
```

### ElasticSearch
```yml
efk_es_svc_name: "Service name of ElasticSearch"
efk_es_replicas: "# of ElasticSearch replicas"
efk_es_image_repo: "ElasticSearch image repository"
efk_es_image_tag: "ElasticSearch image tag"
efk_busybox_image_repo: "Busybox image repository"
efk_busybox_image_tag: "Busybox image tag"
efk_es_volume_size: "Volume size for ElasticSearch"
```

### Kibana
```yml
efk_kibana_service_type: "type of service object, e.g. LoadBalancer, CluterIP, NodePort"
efk_kibana_replicas: "# of Kibana replicas"
efk_kibana_image_repo: "Kibana image repository"
efk_kibana_image_tag: "Kibana image tag"
efk_hyperauth_url: "Hyperauth URL"
efk_hyperauth_realm: "Hyperauth relam name for EFK Kibana"
efk_kibana_client_id: "Hyperauth client id for EFK Kibana"
efk_kibana_encryption_key: "Encryption key for session encoding"
```

### Encryption key 관련 참고 자료
[docs](https://gogatekeeper.github.io/configuration/#encryption-key)

### Fluentd
```yml
efk_fluentd_image: "image for Fluentd container"
```

### 예시

```yml
efk_namespace: kube-logging

efk_es_svc_name: "elasticsearch"
efk_es_replicas: 1
efk_es_image_repo: "docker.elastic.co/elasticsearch/elasticsearch"
efk_es_image_tag: "7.2.0"
efk_busybox_image_repo: "busybox"
efk_busybox_image_tag: "1.32.0"
efk_es_volume_size: "50Gi"

efk_kibana_service_type: "ClusterIP"
efk_kibana_replicas: 1
efk_kibana_image_repo: "docker.elastic.co/kibana/kibana"
efk_kibana_image_tag: "7.2.0"
efk_gatekeeper_image_repo: "quay.io/keycloak/keycloak-gatekeeper"
efk_gatekeeper_image_tag: "10.0.0"
efk_hyperauth_url: hyperauth.tmaxcloud.org
efk_hyperauth_realm: "tmax"
efk_kibana_client_id: "kibana"
efk_kibana_encryption_key: "AgXa7xRcoClDEU0ZDSH4X0XhL5Qy2Z2j"

efk_fluentd_image_repo: "fluent/fluentd-kubernetes-daemonset"
efk_fluentd_image_tag: "v1.4.2-debian-elasticsearch-1.1"
```