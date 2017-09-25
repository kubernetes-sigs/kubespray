${connection_strings_master}
${connection_strings_node}
${connection_strings_etcd}


${public_ip_address_bastion}

[kube-master]
${list_master}


[kube-node]
${list_node}


[etcd]
${list_etcd}


[k8s-cluster:children]
kube-node
kube-master


[k8s-cluster:vars]
${elb_api_fqdn}
${elb_api_port}
${kube_insecure_apiserver_address}
