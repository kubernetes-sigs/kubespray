[all]
${connection_strings_controlplane}
${connection_strings_node}
${connection_strings_etcd}
${public_ip_address_bastion}

[bastion]
${public_ip_address_bastion}

[kube-controlplane]
${list_controlplane}


[kube-node]
${list_node}


[etcd]
${list_etcd}


[k8s-cluster:children]
kube-node
kube-controlplane


[k8s-cluster:vars]
${elb_api_fqdn}
