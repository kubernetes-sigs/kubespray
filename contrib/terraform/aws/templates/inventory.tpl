[all]
${connection_strings_master}
${connection_strings_node}
${connection_strings_etcd}
${public_ip_address_bastion}

[bastion]
${public_ip_address_bastion}

[kube_control_plane]
${list_master}


[kube_node]
${list_node}


[etcd]
${list_etcd}


[k8s_cluster:children]
kube_node
kube_control_plane


[k8s_cluster:vars]
${elb_api_fqdn}
