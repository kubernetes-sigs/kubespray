CephFS Volume Provisioner for Kubernetes 1.5+
=============================================

[![Docker Repository on Quay](https://quay.io/repository/external_storage/cephfs-provisioner/status "Docker Repository on Quay")](https://quay.io/repository/external_storage/cephfs-provisioner)

Using Ceph volume client

Development
-----------

Compile the provisioner

``` console
make
```

Make the container image and push to the registry

``` console
make push
```

Test instruction
----------------

-   Start Kubernetes local cluster

See <a href="https://kubernetes.io/" class="uri" class="uri">https://kubernetes.io/</a>.

-   Create a Ceph admin secret

``` bash
ceph auth get client.admin 2>&1 |grep "key = " |awk '{print  $3'} |xargs echo -n > /tmp/secret
kubectl create ns cephfs
kubectl create secret generic ceph-secret-admin --from-file=/tmp/secret --namespace=cephfs
```

-   Start CephFS provisioner

The following example uses `cephfs-provisioner-1` as the identity for the instance and assumes kubeconfig is at `/root/.kube`. The identity should remain the same if the provisioner restarts. If there are multiple provisioners, each should have a different identity.

``` bash
docker run -ti -v /root/.kube:/kube -v /var/run/kubernetes:/var/run/kubernetes --privileged --net=host cephfs-provisioner /usr/local/bin/cephfs-provisioner -master=http://127.0.0.1:8080 -kubeconfig=/kube/config -id=cephfs-provisioner-1
```

Alternatively, deploy it in kubernetes, see [deployment](deploy/README.md).

-   Create a CephFS Storage Class

Replace Ceph monitor's IP in <a href="example/class.yaml" class="uri" class="uri">example/class.yaml</a> with your own and create storage class:

``` bash
kubectl create -f example/class.yaml
```

-   Create a claim

``` bash
kubectl create -f example/claim.yaml
```

-   Create a Pod using the claim

``` bash
kubectl create -f example/test-pod.yaml
```

Known limitations
-----------------

-   Kernel CephFS doesn't work with SELinux, setting SELinux label in Pod's securityContext will not work.
-   Kernel CephFS doesn't support quota or capacity, capacity requested by PVC is not enforced or validated.
-   Currently each Ceph user created by the provisioner has `allow r` MDS cap to permit CephFS mount.

Acknowledgement
---------------

Inspired by CephFS Manila provisioner and conversation with John Spray
