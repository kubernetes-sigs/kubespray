# Registry Operator

Edit inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml

```yml
registry_operator_enabled: false
# registry_operator_ingress_nginx_class: nginx
# registry_operator_storage_class: "" # empty will use default storage class
```

* **registry_operator_enabled**: whether to install or not
* **registry_operator_ingress_nginx_class**: Ingress class name to be used for
* **registry_operator_storage_class**: The name of StorageClass for creating PVC

## Prerequsite

* [community.crpyto collection](https://galaxy.ansible.com/community/crypto)  ([Download](https://galaxy.ansible.com/download/community-crypto-1.9.2.tar.gz))

### Collection 오프라인 설치 ([참고](https://www.redhat.com/sysadmin/install-ansible-disconnected-node))

1. ansible.cfg에 다음과 같이 COLLECTIONS_PATHS 엔트리를 추가한다

```text
[defaults]
inventory = ./inventory
COLLECTIONS_PATHS = ./collections
```

2. kubespray 홈 디렉터리에 collections 디렉터리를 추가한다
```bash
mkdir -p ./collections/ansible_collections/community/crpyto
```

3. 다운로드 받은 아카이브를 해제한다.
```bash
tar -xf ~/Downloads/community-crypto-1.9.2.tar.gz \
  -C collections/ansible_collections/community/crpyto
```

4. collection을 올바로 참조할 수 있는지 확인한다.
```bash
ansible-galaxy collection list
```