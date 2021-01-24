[all]
${connection_strings_master}
${connection_strings_worker}

[kube-master]
${list_master}

[kube-master:vars]
supplementary_addresses_in_ssl_keys = [ "${api_lb_ip_address}" ]

[etcd]
${list_master}

[kube-node]
${list_worker}

[k8s-cluster:children]
kube-master
kube-node
