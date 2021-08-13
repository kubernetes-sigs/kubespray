# Image Validating Webhook

kubespray로 Image Validating Webhook 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml 에서 설정한다.

```yml
image_validating_webhook_namespace: image validating webhook pod를 배포 할 namespace의 이름
image_validating_webhook_image: pod의 배포에 사용할 image의 이름
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```bash
---

```
