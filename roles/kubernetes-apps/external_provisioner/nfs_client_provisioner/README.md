# NFS Client provisioner

`nfs-client` is an out-of-tree dynamic provisioner for Kubernetes.
[nfs-client](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs-client)
You can use it to quickly and easily leverage an already existing NFS share to provide 
dynamic provisioning of Kubernetes Persistent Volumes via Persistent Volume Claims

It works just like in-tree dynamic provisioner. For more information on how
dynamic provisioning works, see [the docs](http://kubernetes.io/docs/user-guide/persistent-volumes/)
or [this blog post](http://blog.kubernetes.io/2016/10/dynamic-provisioning-and-storage-in-kubernetes.html).

## Acknowledgements

- This provisioner is extracted from [Kubernetes incubator](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs-client)
with some modifications for this project.
