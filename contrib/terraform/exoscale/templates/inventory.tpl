[all]
${connection_strings_master}
${connection_strings_worker}

[kube_control_plane]
${list_master}

[kube_control_plane:vars]
supplementary_addresses_in_ssl_keys = [ "${api_lb_ip_address}" ]

[etcd]
${list_master}

[kube_node]
${list_worker}

[k8s_cluster:children]
kube_control_plane
kube_node
