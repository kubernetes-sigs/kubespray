# vSphere CSI Driver

vSphere CSI driver allows you to provision volumes over a vSphere deployment. The Kubernetes historic in-tree cloud provider was deprecated in Kubernetes 1.19 and removed in 1.30.

## Prerequisites

The vSphere user for CSI driver requires a set of privileges to perform Cloud Native Storage operations. Follow the [official guide](https://vsphere-csi-driver.sigs.k8s.io/driver-deployment/prerequisites.html#roles_and_privileges) to configure those.

## Kubespray configuration

To enable vSphere CSI driver, uncomment the `vsphere_csi_enabled` option in `group_vars/all/vsphere.yml` and set it to `true`.

To set the number of replicas for the vSphere CSI controller, you can change `vsphere_csi_controller_replicas` option in `group_vars/all/vsphere.yml`.

You need to source the vSphere credentials you use to deploy your machines that will host Kubernetes.

Note that these components have supported Kubernetes versions and supported vSphere versions. In particular:

- `external_vsphere_cloud_controller_image_tag` should follow the version of Kubernetes. Available versions can be found [in the README](https://github.com/kubernetes/cloud-provider-vsphere/blob/master/README.md).
- `vsphere_csi_controller` support a window of three versions of Kubernetes, but also have minimum versions of vSphere to follow. Check [the docs here](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/container-storage-plugin/3-0/getting-started-with-vmware-vsphere-container-storage-plug-in-3-0/vsphere-container-storage-plug-in-concepts/compatibility-matrix-for-vsphere-container-storage-plug-in.html#GUID-D4AAD99E-9128-40CE-B89C-AD451DA8379D-en) to make sure you have a supported version.

Kubespray may update these defaults to the latest versions, but can not know what version of vSphere you are using and does not try to match Kubernetes versions to supported vSphere component versions. You should pin these to supported versions in your environment, and update them along with Kubernetes and Kubespray.

| Variable                                        | Required | Type    | Choices         | Default                 | Comment                                                                                                                     |
|-------------------------------------------------|----------|---------|-----------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| external_vsphere_vcenter_ip                     | TRUE     | string  |                 |                         | IP/URL of the vCenter                                                                                                       |
| external_vsphere_vcenter_port                   | TRUE     | string  |                 | "443"                   | Port of the vCenter API                                                                                                     |
| external_vsphere_insecure                       | TRUE     | string  | "true", "false" | "true"                  | set to "true" if the host above uses a self-signed cert                                                                     |
| external_vsphere_user                           | TRUE     | string  |                 |                         | User name for vCenter with required privileges (Can also be specified with the `VSPHERE_USER` environment variable)         |
| external_vsphere_password                       | TRUE     | string  |                 |                         | Password for vCenter (Can also be specified with the `VSPHERE_PASSWORD` environment variable)                               |
| external_vsphere_datacenter                     | TRUE     | string  |                 |                         | Datacenter name to use                                                                                                      |
| external_vsphere_kubernetes_cluster_id          | TRUE     | string  |                 | "kubernetes-cluster-id" | Kubernetes cluster ID to use                                                                                                |
| external_vsphere_version                        | TRUE     | string  |                 | "7.0u1"                 | Vmware Vsphere version where located all VMs                                                                                |
| external_vsphere_cloud_controller_image_tag     | TRUE     | string  |                 | "v1.34.0"               | CPI manager image tag to use                                                                                                |
| vsphere_syncer_image_tag                        | TRUE     | string  |                 | "v3.6.0"                | Syncer image tag to use                                                                                                     |
| vsphere_csi_attacher_image_tag                  | TRUE     | string  |                 | "v4.9.0"                | CSI attacher image tag to use                                                                                               |
| vsphere_csi_controller                          | TRUE     | string  |                 | "v3.6.0"                | CSI controller image tag to use                                                                                             |
| vsphere_csi_controller_replicas                 | TRUE     | integer |                 | 1                       | Number of pods Kubernetes should deploy for the CSI controller                                                              |
| vsphere_csi_liveness_probe_image_tag            | TRUE     | string  |                 | "v2.15.0"               | CSI liveness probe image tag to use                                                                                         |
| vsphere_csi_provisioner_image_tag               | TRUE     | string  |                 | "v4.0.1"                | CSI provisioner image tag to use                                                                                            |
| vsphere_csi_snapshotter_image_tag               | TRUE     | string  |                 | "v8.2.0"                | CSI snapshotter image tag to use                                                                                            |
| vsphere_csi_node_driver_registrar_image_tag     | TRUE     | string  |                 | "v2.13.0"               | CSI node driver registrar image tag to use                                                                                  |
| vsphere_csi_driver_image_tag                    | TRUE     | string  |                 | "v3.6.0"                | CSI driver image tag to use                                                                                                 |
| vsphere_csi_resizer_tag                         | TRUE     | string  |                 | "v1.12.0"               | CSI resizer image tag to use                                                                                                |
| vsphere_csi_aggressive_node_drain               | FALSE    | boolean |                 | false                   | Enable aggressive node drain strategy                                                                                       |
| vsphere_csi_aggressive_node_unreachable_timeout | FALSE    | int     |                 | 300                     | Timeout till node will be drained when it in an unreachable state                                                           |
| vsphere_csi_aggressive_node_not_ready_timeout   | FALSE    | int     |                 | 300                     | Timeout till node will be drained when it in not-ready state                                                                |
| vsphere_csi_namespace                           | TRUE     | string  |                 | "kube-system"           | vSphere CSI namespace to use; kube-system for backward compatibility, should be change to vmware-system-csi on the long run |

## Usage example

To test the dynamic provisioning using vSphere CSI driver, make sure to create a [storage policy](https://github.com/kubernetes/cloud-provider-vsphere/blob/master/docs/book/tutorials/kubernetes-on-vsphere-with-kubeadm.md#create-a-storage-policy) and [storage class](https://github.com/kubernetes/cloud-provider-vsphere/blob/master/docs/book/tutorials/kubernetes-on-vsphere-with-kubeadm.md#create-a-storageclass), then apply the following manifest:

```yml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: csi-pvc-vsphere
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: mongodb-sc

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
      - mountPath: /usr/share/nginx/html
        name: csi-data-vsphere
  volumes:
  - name: csi-data-vsphere
    persistentVolumeClaim:
      claimName: csi-pvc-vsphere
      readOnly: false
```

Apply this conf to your cluster: ```kubectl apply -f nginx.yml```

You should see the PVC provisioned and bound:

```ShellSession
$ kubectl get pvc
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
csi-pvc-vsphere   Bound    pvc-dc7b1d21-ee41-45e1-98d9-e877cc1533ac   1Gi        RWO            mongodb-sc     10s
```

And the volume mounted to the Nginx Pod (wait until the Pod is Running):

```ShellSession
kubectl exec -it nginx -- df -h | grep /usr/share/nginx/html
/dev/sdb         976M  2.6M  907M   1% /usr/share/nginx/html
```

## More info

For further information about the vSphere CSI Driver, you can refer to the official [vSphere Cloud Provider documentation](https://cloud-provider-vsphere.sigs.k8s.io/container_storage_interface.html).
