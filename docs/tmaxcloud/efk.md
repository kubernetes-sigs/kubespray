# EFK

Kubespray 를 통해 EFK 배포를 하기 위해서는 아래의 parameter 들을 설정해야 한다.

### Common
```yml
efk_namespace: "namespace for EFK stack"
```

### ElasticSearch
```yml
efk_es_replicas: "# of ElasticSearch replicas"
efk_es_image: "image for ElasticSearch container"
efk_busybox_image: "image for busybox (init container for ElasticSearch"
efk_es_volume_size: "volume size for ElasticSearch"
```

### Kibana
```yml
efk_kibana_service_type: "type of service object, e.g. LoadBalancer, NodePort"
efk_kibana_replicas: "# of Kibana replicas"
efk_kibana_image: "image for Kibana container"
```

### Fluentd
```yml
efk_fluentd_image: "image for Fluentd container"
```

### 예시

```yml
efk_namespace: kube-logging

efk_es_replicas: 3
efk_es_image: docker.elastic.co/elasticsearch/elasticsearch:7.2.0
efk_busybox_image: busybox:1.32.0
efk_es_volume_size: 50Gi

efk_kibana_service_type: NodePort
efk_kibana_replicas: 1
efk_kibana_image: docker.elastic.co/kibana/kibana:7.2.0

efk_fluentd_image: fluent/fluentd-kubernetes-daemonset:v1.4.2-debian-elasticsearch-1.1
```

