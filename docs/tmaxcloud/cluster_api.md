# Cluster API

kubespray로 Cluster API 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같다.

```yml
cluster_api_enabled: Cluster API 설치 여부(true/false)

cluster_api_provider_aws: Cluster API provider AWS 설치 여부(true/false)
cluster_api_aws_access_key: AWS ACCESS KEY값
cluster_api_aws_secret_key: AWS SECRET KEY값
cluster_api_aws_region: AWS REGION

cluster_api_provider_vsphere: Cluster API provider vSphere 설치 여부(true/false)
cluster_api_vsphere_username: vCenter 계정
cluster_api_vsphere_password: vCenter 비밀번호
```


### 예시
```yml
cluster_api_enabled: true

cluster_api_provider_aws: true
cluster_api_aws_access_key: "AAAAAAAAAAAAAAAAAAAA"
cluster_api_aws_secret_key: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
cluster_api_aws_region: "us-east-1"

cluster_api_provider_vsphere: true
cluster_api_vsphere_username: "user@vsphere.local" 
cluster_api_vsphere_password: "0000"
```
