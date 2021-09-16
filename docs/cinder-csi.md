# Cinder CSI Driver

Cinder CSI driver allows you to provision volumes over an OpenStack deployment. The Kubernetes historic in-tree cloud provider is deprecated and will be removed in future versions.

To enable Cinder CSI driver, uncomment the `cinder_csi_enabled` option in `group_vars/all/openstack.yml` and set it to `true`.

To set the number of replicas for the Cinder CSI controller, you can change `cinder_csi_controller_replicas` option in `group_vars/all/openstack.yml`.

You need to source the OpenStack credentials you use to deploy your machines that will host Kubernetes: `source path/to/your/openstack-rc` or `. path/to/your/openstack-rc`.

Make sure the hostnames in your `inventory` file are identical to your instance names in OpenStack. Otherwise [cinder](https://docs.openstack.org/cinder/latest/) won't work as expected.

If you want to deploy the cinder provisioner used with Cinder CSI Driver, you should set `persistent_volumes_enabled` in `group_vars/k8s_cluster/k8s_cluster.yml` to `true`.

You can now run the kubespray playbook (cluster.yml) to deploy Kubernetes over OpenStack with Cinder CSI Driver enabled.

## Usage example

To check if Cinder CSI Driver works properly, see first that the cinder-csi pods are running:

```ShellSession
$ kubectl -n kube-system get pods | grep cinder
csi-cinder-controllerplugin-7f8bf99785-cpb5v   5/5     Running   0          100m
csi-cinder-nodeplugin-rm5x2                    2/2     Running   0          100m
```

Check the associated storage class (if you enabled persistent_volumes):

```ShellSession
$ kubectl get storageclass
NAME         PROVISIONER                AGE
cinder-csi   cinder.csi.openstack.org   100m
```

You can run a PVC and an Nginx Pod using this file `nginx.yaml`:

```yml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: csi-pvc-cinderplugin
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: cinder-csi

---
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - image: nginx
    imagePullPolicy: IfNotPresent
    name: nginx
    ports:
    - containerPort: 80
      protocol: TCP
    volumeMounts:
      - mountPath: /var/lib/www/html
        name: csi-data-cinderplugin
  volumes:
  - name: csi-data-cinderplugin
    persistentVolumeClaim:
      claimName: csi-pvc-cinderplugin
      readOnly: false
```

Apply this conf to your cluster: ```kubectl apply -f nginx.yml```

You should see the PVC provisioned and bound:

```ShellSession
$ kubectl get pvc
NAME                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
csi-pvc-cinderplugin   Bound    pvc-f21ad0a1-5b7b-405e-a462-48da5cb76beb   1Gi        RWO            cinder-csi     8s
```

And the volume mounted to the Nginx Pod (wait until the Pod is Running):

```ShellSession
kubectl exec -it nginx -- df -h | grep /var/lib/www/html
/dev/vdb        976M  2.6M  958M   1% /var/lib/www/html
```

## Compatibility with in-tree cloud provider

It is not necessary to enable OpenStack as a cloud provider for Cinder CSI Driver to work.
Though, you can run both the in-tree openstack cloud provider and the Cinder CSI Driver at the same time. The storage class provisioners associated to each one of them are differently named.

## Cinder v2 support

For the moment, only Cinder v3 is supported by the CSI Driver.

## More info

For further information about the Cinder CSI Driver, you can refer to this page: [Cloud Provider OpenStack](https://github.com/kubernetes/cloud-provider-openstack/blob/master/docs/using-cinder-csi-plugin.md).
