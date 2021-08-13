# Hypercloud

kubespray로 Hypercloud 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같다.

```yml
hypercloud_enabled: hypercloud 설치 여부 (true/false)
hypercloud_hpcd_mode: hypercloud-multi-operator 설치 여부 (single/multi)
hypercloud_hpcd_single_operator_version: hypercloud-single-operator의 버전
hypercloud_hpcd_multi_operator_version: hypercloud-multi-operator의 버전
hypercloud_hpcd_api_server_version: hypercloud-api-server의 버전
hypercloud_hpcd_template_version: template의 버전
hypercloud_kafka1_addr: kafka pod의 주소 (같은 클러스터인 경우 "DNS" 입력)
hypercloud_kafka2_addr: kafka pod의 주소
hypercloud_kafka3_addr: kafka pod의 주소
```


### 예시
```yml
hypercloud_enabled: true 
hypercloud_hpcd_mode: "multi"
hypercloud_hpcd_single_operator_version: "5.0.20.1"
hypercloud_hpcd_multi_operator_version: "5.0.20.0"
hypercloud_hpcd_api_server_version: "5.0.20.0"
hypercloud_hpcd_template_version: "5.0.0.0"
hypercloud_kafka1_addr: "DNS"
hypercloud_kafka2_addr: "DNS"
hypercloud_kafka3_addr: "DNS"
```
