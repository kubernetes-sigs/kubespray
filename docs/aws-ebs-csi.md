# AWS EBS CSI Driver

AWS EBS CSI driver allows you to provision EBS volumes for pods in EC2 instances. The old in-tree AWS cloud provider is deprecated and will be removed in future versions of Kubernetes. So transitioning to the CSI driver is advised.

To enable AWS EBS CSI driver, uncomment the `aws_ebs_csi_enabled` option in `group_vars/all/aws.yml` and set it to `true`.

To set the number of replicas for the AWS CSI controller, you can change `aws_ebs_csi_controller_replicas` option in `group_vars/all/aws.yml`.

Make sure to add a role, for your EC2 instances hosting Kubernetes, that allows it to do the actions necessary to request a volume and attach it: [AWS CSI Policy](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/docs/example-iam-policy.json)

If you want to deploy the AWS EBS storage class used with the CSI Driver, you should set `persistent_volumes_enabled` in `group_vars/k8s_cluster/k8s_cluster.yml` to `true`.

You can now run the kubespray playbook (cluster.yml) to deploy Kubernetes over AWS EC2 with EBS CSI Driver enabled.

## Usage example

To check if AWS EBS CSI Driver is deployed properly, check that the ebs-csi pods are running:

```ShellSession
$ kubectl -n kube-system get pods | grep ebs
ebs-csi-controller-85d86bccc5-8gtq5                                  4/4     Running   4          40s
ebs-csi-node-n4b99                                                   3/3     Running   3          40s
```

Check the associated storage class (if you enabled persistent_volumes):

```ShellSession
$ kubectl get storageclass
NAME         PROVISIONER                AGE
ebs-sc   ebs.csi.aws.com   45s
```

You can run a PVC and an example Pod using this file `ebs-pod.yml`:

```yml
--
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: centos
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo $(date -u) >> /data/out.txt; sleep 5; done"]
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: ebs-claim
```

Apply this conf to your cluster: ```kubectl apply -f ebs-pod.yml```

You should see the PVC provisioned and bound:

```ShellSession
$ kubectl get pvc
NAME                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
ebs-claim   Bound    pvc-0034cb9e-1ddd-4b3f-bb9e-0b5edbf5194c   1Gi        RWO            ebs-sc         50s
```

And the volume mounted to the example Pod (wait until the Pod is Running):

```ShellSession
$ kubectl exec -it app -- df -h | grep data
/dev/nvme1n1   1014M   34M  981M   4% /data
```

## More info

For further information about the AWS EBS CSI Driver, you can refer to this page: [AWS EBS Driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/).
