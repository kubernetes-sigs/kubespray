# GCP Load Balancers for type=LoadBalacer of Kubernetes Services

> **Removed**: Since v1.31 (the Kubespray counterpart is v2.27), Kubernetes no longer supports `cloud_provider`. (except external cloud provider)

Google Cloud Platform can be used for creation of Kubernetes Service Load Balancer.

This feature is able to deliver by adding parameters to `kube-controller-manager` and `kubelet`. You need specify:

```ShellSession
    --cloud-provider=gce
    --cloud-config=/etc/kubernetes/cloud-config
```

To get working it in kubespray, you need to add tag to GCE instances and specify it in kubespray group vars and also set `cloud_provider` to `gce`. So for example, in file `group_vars/all/gcp.yml`:

```yaml
    cloud_provider: gce
    gce_node_tags: k8s-lb
```

When you will setup it and create SVC in Kubernetes with `type=LoadBalancer`, cloud provider will create public IP and will set firewall.
Note: Cloud provider run under VM service account, so this account needs to have correct permissions to be able to create all GCP resources.
