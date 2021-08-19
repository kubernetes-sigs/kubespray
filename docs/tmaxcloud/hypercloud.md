# Hypercloud

kubespray로 Hypercloud 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같다.

```yml
hypercloud_enabled: hypercloud 설치 여부 (true/false)
```

Hypercloud 설치를 위해 사용되는 이미지의 경로와 태그는 roles/download/defaults/main.yml에 정의되어있다.

1. Hypercloud Api Server
```yml
hypercloud_postgres_image_repo: "{{ docker_image_repo }}/tmaxcloudck/postgres-cron"
hypercloud_postgres_image_tag: "b5.0.0.1"
hypercloud_api_server_image_repo: "{{ docker_image_repo }}/tmaxcloudck/hypercloud-api-server"
hypercloud_api_server_image_tag: "b5.0.23.0"
hypercloud_fluent_sidecar_image_repo: "fluent/fluent-bit"
hypercloud_fluent_sidecar_image_tag: "1.5-debug"
```

2. Hypercloud Single Operator
```yml
hypercloud_single_operator_image_repo: "{{ docker_image_repo }}/tmaxcloudck/hypercloud-single-operator"
hypercloud_operator_proxy_image_repo: "{{ gcr_image_repo }}/kubebuilder/kube-rbac-proxy"
hypercloud_operator_proxy_image_tag: "v0.5.0"
```

3. Hypercloud Multi Operator
```yml
hypercloud_multi_operator_image_repo: "{{ docker_image_repo }}/tmaxcloudck/hypercloud-single-operator"
hypercloud_operator_proxy_image_repo: "{{ gcr_image_repo }}/kubebuilder/kube-rbac-proxy"
hypercloud_operator_proxy_image_tag: "v0.5.0"
```

4. Template(Vsphere)
```yml
hypercloud_vsphere_cpi_image_repo: "{{ gcr_image_repo }}/cloud-provider-vsphere/cpi/release/manager"
hypercloud_vsphere_cpi_image_tag: "v1.18.1"
hypercloud_vsphere_kube_vip_repo: "plndr/kube-vip"
hypercloud_vsphere_kube_vip_tag: "0.3.2"
hypercloud_vsphere_node_driver_repo: "{{ quay_image_repo }}/k8scsi/csi-node-driver-registrar"
hypercloud_vsphere_node_driver_tag: "v2.0.1"
hypercloud_vsphere_csi_driver_image_repo: "{{ gcr_image_repo }}/cloud-provider-vsphere/csi/release/driver"
hypercloud_vsphere_csi_driver_image_tag: "v2.1.0"
hypercloud_vsphere_csi_livenessprobe_image_repo: "{{ quay_image_repo }}/k8scsi/livenessprobe"
hypercloud_vsphere_csi_livenessprobe_image_tag: "v2.1.0"
hypercloud_vsphere_csi_attacher_image_repo: "{{ quay_image_repo }}/k8scsi/csi-attacher"
hypercloud_vsphere_csi_attacher_image_tag: "v3.0.0"
hypercloud_vsphere_csi_syncer_image_repo: "{{ gcr_image_repo }}/cloud-provider-vsphere/csi/release/syncer"
hypercloud_vsphere_csi_syncer_image_tag: "v2.1.0"
hypercloud_vsphere_csi_provisioner_image_repo: "{{ quay_image_repo }}/k8scsi/csi-provisioner"
hypercloud_vsphere_csi_provisioner_image_tag: "v2.0.0"
```