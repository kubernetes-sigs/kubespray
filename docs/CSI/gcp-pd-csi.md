# GCP Persistent Disk CSI Driver

The GCP Persistent Disk CSI driver allows you to provision volumes for pods with a Kubernetes deployment over Google Cloud Platform. The CSI driver replaces to volume provioning done by the in-tree azure cloud provider which is deprecated.

To deploy GCP Persistent Disk CSI driver, uncomment the `gcp_pd_csi_enabled` option in `group_vars/all/gcp.yml` and set it to `true`.

## GCP Persistent Disk Storage Class

If you want to deploy the GCP Persistent Disk storage class to provision volumes dynamically, you should set `persistent_volumes_enabled` in `group_vars/k8s_cluster/k8s_cluster.yml` to `true`.

## GCP credentials

In order for the CSI driver to provision disks, you need to create for it a service account on GCP with the appropriate permissions.

Follow these steps to configure it:

```ShellSession
# This will open a web page for you to authenticate
gcloud auth login
export PROJECT=nameofmyproject
gcloud config set project $PROJECT

git clone https://github.com/kubernetes-sigs/gcp-compute-persistent-disk-csi-driver $GOPATH/src/sigs.k8s.io/gcp-compute-persistent-disk-csi-driver

export GCE_PD_SA_NAME=my-gce-pd-csi-sa
export GCE_PD_SA_DIR=/my/safe/credentials/directory

./deploy/setup-project.sh
```

The above will create a file named `cloud-sa.json` in the specified `GCE_PD_SA_DIR`. This file contains the service account with the appropriate credentials for the CSI driver to perform actions on GCP to request disks for pods.

You need to provide this file's path through the variable `gcp_pd_csi_sa_cred_file` in `inventory/mycluster/group_vars/all/gcp.yml`

You can now deploy Kubernetes with Kubespray over GCP.

## GCP PD CSI Driver test

To test the dynamic provisioning using GCP PD CSI driver, make sure to have the storage class deployed (through persistent volumes), and apply the following manifest:

```yml
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: podpvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: csi-gce-pd
  resources:
    requests:
      storage: 1Gi

---
apiVersion: v1
kind: Pod
metadata:
  name: web-server
spec:
  containers:
   - name: web-server
     image: nginx
     volumeMounts:
       - mountPath: /var/lib/www/html
         name: mypvc
  volumes:
   - name: mypvc
     persistentVolumeClaim:
       claimName: podpvc
       readOnly: false
```

## GCP PD documentation

You can find the official GCP Persistent Disk CSI driver installation documentation here: [GCP PD CSI Driver](https://github.com/kubernetes-sigs/gcp-compute-persistent-disk-csi-driver/blob/master/docs/kubernetes/user-guides/driver-install.md
)
