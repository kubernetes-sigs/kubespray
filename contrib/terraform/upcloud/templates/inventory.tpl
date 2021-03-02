[all]
${connection_strings_master}
${connection_strings_worker}

[kube-master]
${list_master}

[etcd]
${list_master}

[kube-node]
${list_worker}

[k8s-cluster:children]
kube-master
kube-node
