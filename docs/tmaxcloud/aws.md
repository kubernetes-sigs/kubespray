## 구성 요소 및 버전
  * Terraform v1.1.2

## aws 환경 구축 가이드

1. (aws 인스턴스가 없는 경우) 아래 링크의 terraform 가이드를 참고 하여 인스턴스를 생성한다.
* https://github.com/tmax-cloud/kubespray/blob/tmax-master/contrib/terraform/aws/docs/README.md

2. terraform apply 후 생성된 hosts 파일을 참고하여 kubespray 설정을 한다.

* apiserver_loadbalancer_domain_name을 수정한다. (inventory/tmaxcloud/group_vars/all/all.yml)

```yml
apiserver_loadbalancer_domain_name: "{{apiserver_loadbalancer_domain_name}}"
loadbalancer_apiserver:
  port: 6443

ex)
## External LB example config
apiserver_loadbalancer_domain_name: "kubernetes-nlb-supercloud-43e596a4155bc464.elb.ap-northeast-1.amazonaws.com"
loadbalancer_apiserver:
  port: 6443
```

* aws-efs-csi-driver을 수정한다. (inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml)

```yml
ex)
# aws-efs-csi-driver
aws_efs_csi_enabled: true
aws_efs_csi_namespace: aws-efs-csi
aws_efs_csi_filesystem_id: fs-01f418ae6c17a6ae4
aws_efs_csi_controller_replicas: 1
```
