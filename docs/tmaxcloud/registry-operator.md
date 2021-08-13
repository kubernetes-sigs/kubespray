# Registry Operator

Edit inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml

```yml
registry_operator_enabled: false
# registry_operator_ingress_nginx_class: nginx
# registry_operator_storage_class: "" # empty will use default storage class
# registry_operator_disk_size: 50G
```

* **registry_operator_enabled**: whether to install or not
* **registry_operator_ingress_nginx_class**: Ingress class name to be used for 
* **registry_operator_storage_class**: The name of StorageClass for creating PVC
* **registry_operator_disk_size**: A size of storage for container images