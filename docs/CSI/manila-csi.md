# Manila CSI Driver

The Manila CSI driver allows you to provision shared filesystems backed by [OpenStack Manila](https://docs.openstack.org/manila/latest/). It is deployed from the upstream [openstack-manila-csi](https://github.com/kubernetes/cloud-provider-openstack/tree/master/charts/manila-csi-plugin) Helm chart, so Kubespray does not carry a copy of the driver manifests. Only the CephFS share protocol has been tested.

Manila CSI does not mount shares itself: it forwards the node operations to a lower-level CSI driver. For CephFS this is the [ceph-csi](https://github.com/ceph/ceph-csi) node plugin, which Kubespray deploys alongside the chart. The forwarding node plugin must be running before the Manila node plugin, so this role waits for it before installing the chart.

To enable the Manila CSI driver, uncomment the `manila_csi_enabled` option in `group_vars/all/openstack.yml` and set it to `true`. The chart is installed with Helm, so `helm_enabled` must also be set to `true`.

You need to source the OpenStack credentials you use to deploy your machines that will host Kubernetes: `source path/to/your/openstack-rc` or `. path/to/your/openstack-rc`. These credentials are stored in the `csi-manila-secrets` secret and referenced by the storage class.

The control plane node must be able to reach the chart repository `https://kubernetes.github.io/cloud-provider-openstack`, directly or through the configured `http_proxy` / `https_proxy`.

If you want to deploy the Manila storage class, set `persistent_volumes_enabled` in `group_vars/k8s_cluster/k8s_cluster.yml` to `true`, and make sure the share `type` in `manila_storage_classes` matches a share type available in your cloud (`openstack share type list`).

You can now run the Kubespray playbook (cluster.yml) to deploy Kubernetes over OpenStack with the Manila CSI driver enabled.

## Controller replicas

Unlike the Cinder CSI chart, the upstream Manila CSI chart runs the controller plugin as a single-replica StatefulSet with no leader election, so it is not possible to run several active controller replicas. The impact is limited because the controller is not on the data path: running pods keep their mounts if the controller restarts, and only new provisioning, resize and snapshot operations wait for it to come back.

## Scheduling on tainted nodes

Manila shares are mounted by two DaemonSets: the Manila node plugin, deployed by the chart, and the CephFS forwarding plugin. Neither tolerates node taints by default, so they do not run on control planes, and pods scheduled there cannot mount Manila shares.

If you run such workloads on tainted nodes, set `manila_csi_node_tolerations` in your inventory. The value applies to both DaemonSets, so they stay consistent:

```yaml
manila_csi_node_tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

## Air-gapped installations

The images deployed by the Helm chart follow `kube_image_repo`, and the ceph-csi forwarding plugin image follows `quay_image_repo`. Pointing those two variables at your internal mirror is enough; no Manila-specific override is needed.

The chart itself is still fetched from the repository mentioned above, which must remain reachable from the control plane.

## Usage example

Once the driver is deployed, the Manila and CephFS forwarding pods run in the `kube-system` namespace:

```ShellSession
$ kubectl -n kube-system get pods | grep -Ei 'manila|cephfs'
csi-cephfs-nodeplugin-2b9s2                    1/1     Running   0               43h
csi-cephfs-nodeplugin-zvxt4                    1/1     Running   0               43h
openstack-manila-csi-controllerplugin-0        4/4     Running   0               43h
openstack-manila-csi-nodeplugin-8dntg          2/2     Running   0               43h
openstack-manila-csi-nodeplugin-plvgd          2/2     Running   0               43h
```

The storage class uses `WaitForFirstConsumer`, so a PVC stays `Pending` until a pod consumes it. Apply the following manifest:

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: manila-test
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: manila-csi
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: manila-test
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["/bin/sh", "-c", "echo ok > /data/test && sleep 3600"]
      volumeMounts:
        - mountPath: /data
          name: manila
  volumes:
    - name: manila
      persistentVolumeClaim:
        claimName: manila-test
```

Once the pod is scheduled, the PVC is bound and a share is created in Manila, which you can check with `openstack share list`.

## Using NFS instead of CephFS

The chart also supports NFS. To use it, the forwarding node plugin must be the NFS one instead of ceph-csi, and `manila_csi_values.shareProtocols` must select `NFS`. The generated CSIDriver is then `nfs.manila.csi.openstack.org`, and the storage class provisioner must be set accordingly. This path has not been tested in Kubespray.
