# aws_efs_csi

kubespray로 aws-efs-csi 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같습니다.

```yml
aws_efs_csi_enabled: aws efs csi 배포 여부 (true/false)
aws_efs_csi_namespace: aws efs csi 를 배포 할 namespace
aws_efs_csi_filesystem_id: 사용 할 efs의 filesystem id (aws에서 확인) 
aws_efs_csi_controller_replicas: aws efs csi controller pod 의 개수
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정합니다.

```yml
aws_efs_csi_enabled: true
aws_efs_csi_namespace: aws-efs-csi
aws_efs_csi_filesystem_id: fs-0fcfea187281e5235
aws_efs_csi_controller_replicas: 1
```

### AWS EFS 사용

EFS 생성 및 사용은 [efs 가이드](https://github.com/tmax-cloud/hypersds-wiki/tree/main/aws_storage_guide) 참고 부탁드립니다.
