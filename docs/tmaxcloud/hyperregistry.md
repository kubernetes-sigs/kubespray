# HyperRegistry

Edit inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml

```yml
hyperregistry_enabled: false
# hyperregistry_ingress_nginx_class: nginx
# hyperregistry_registry_storage_class: ""
# hyperregistry_registry_disk_size: 50G
```

* **hyperregistry_enabled**: whether to install or not
* **hyperregistry_ingress_nginx_class**: Ingress class name to be used for 
* **hyperregistry_registry_storage_class**: The name of StorageClass for creating PVC
* **hyperregistry_registry_disk_size**: A size of storage for container images