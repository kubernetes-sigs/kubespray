
[all]
${connection_strings_master}
${connection_strings_worker}

<<<<<<< HEAD
[kube-master]
=======
[kube_control_plane]
>>>>>>> upstream/master
${list_master}

[etcd]
${list_master}

[kube-node]
${list_worker}

[k8s-cluster:children]
<<<<<<< HEAD
kube-master
=======
kube_control_plane
>>>>>>> upstream/master
kube-node
