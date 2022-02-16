# offline 환경 설정

offline 환경에서의 kubespray 설치를 위해 inventory/tmaxcloud/group_vars/all/offline.yml 을 수정한다.

```yml
is_this_offline: true
registry_host: private registry 주소
files_repo: 구축한 webserver repo 경로
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
is_this_offline: true
registry_host: "10.0.10.50:5000"
files_repo: "http://172.22.5.2"
```

# online 환경 설정

online 환경에서의 kubespray 설치를 위해 inventory/tmaxcloud/group_vars/all/offline.yml 을 수정한다.

```yml
is_this_offline: false
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다. is_this_offline를 제외한 모든 변수들을 주석처리 한다.

```yml
is_this_offline: false

### Private Container Image Registry
#registry_host: "10.0.10.50:5000"
#files_repo: "http://172.22.5.2"
### If using CentOS, RedHat, AlmaLinux or Fedora
# yum_repo: "file:///tmp/packages-repo"
### If using Debian
# debian_repo: "http://myinternaldebianrepo"
### If using Ubuntu
# ubuntu_repo: "http://myinternalubunturepo"

## Container Registry overrides
#kube_image_repo: "{{ registry_host }}/k8s.gcr.io"
#etcd_image_repo: "{{ registry_host }}/k8s.gcr.io"
#gcr_image_repo: "{{ registry_host }}/gcr.io"
#ghcr_image_repo: "{{ registry_host }}/ghcr.io"
#docker_image_repo: "{{ registry_host }}/docker.io"
#quay_image_repo: "{{ registry_host }}/quay.io"
#mcr_image_repo: "{{ registry_host }}/mcr.microsoft.com"
#nvcr_image_repo: "{{ registry_host }}/nvcr.io"
#elastic_image_repo: "{{ registry_host }}/docker.elastic.co"
#us_gcr_image_repo: "{{ registry_host }}/us.gcr.io"
#grafana_image_repo: "{{ registry_host }}/grafana/grafana"
#efk_fluentd_image_repo: "{{ registry_host }}/fluent"
#mysql_image_repo: "{{ registry_host }}/mysql"
#efk_busybox_image_repo: "{{ registry_host }}/busybox"

## Kubernetes components
#kubeadm_download_url: "{{ files_repo }}/kubeadm"
#kubectl_download_url: "{{ files_repo }}/kubectl"
#kubelet_download_url: "{{ files_repo }}/kubelet"

## CNI Plugins
#cni_download_url: "{{ files_repo }}/cni-plugins-linux-amd64-v0.9.1.tgz"

## cri-tools
#crictl_download_url: "{{ files_repo }}/crictl-v1.19.0-linux-amd64.tar.gz"

## [Optional] etcd: only if you **DON'T** use etcd_deployment=host
#etcd_download_url: "{{ files_repo }}/etcd-v3.4.13-linux-amd64.tar.gz"

# [Optional] Calico: If using Calico network plugin
#calicoctl_download_url: "{{ files_repo }}/calicoctl-linux-amd64"

# [Optional] Calico with kdd: If using Calico network plugin with kdd datastore
#calico_crds_download_url: "{{ files_repo }}/calico-3.17.4.tar.gz"

## hyperregistry
#hyperregistry_download_url: "{{ files_repo }}/hyperregistry-v2.2.2.tgz"

# [Optional] helm: only if you set helm_enabled: true
#helm_download_url: "{{ files_repo }}/helm-v3.5.4-linux-amd64.tar.gz"
```
