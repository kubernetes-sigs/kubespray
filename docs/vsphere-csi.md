# vSphere CSI Driver

vSphere CSI driver allows you to provision volumes over a vSphere deployment. The Kubernetes historic in-tree cloud provider is deprecated and will be removed in future versions.

To enable vSphere CSI driver, uncomment the `vsphere_csi_enabled` option in `group_vars/all/vsphere.yml` and set it to `true`.

To set the number of replicas for the vSphere CSI controller, you can change `vsphere_csi_controller_replicas` option in `group_vars/all/vsphere.yml`.

You need to source the vSphere credentials you use to deploy your machines that will host Kubernetes.

| Variable                               | Required | Type    | Choices                    | Default                   | Comment                                                        |
|----------------------------------------|----------|---------|----------------------------|---------------------------|----------------------------------------------------------------|
| external_vsphere_vcenter_ip            | TRUE     | string  |                            |                           | IP/URL of the vCenter                                          |
| external_vsphere_vcenter_port          | TRUE     | string  |                            | "443"                     | Port of the vCenter API                                        |
| external_vsphere_insecure              | TRUE     | string  | "true", "false"            | "true"                    | set to "true" if the host above uses a self-signed cert        |
| external_vsphere_user                  | TRUE     | string  |                            |                           | User name for vCenter with required privileges                 |
| external_vsphere_password              | TRUE     | string  |                            |                           | Password for vCenter                                           |
| external_vsphere_datacenter            | TRUE     | string  |                            |                           | Datacenter name to use                                         |
| external_vsphere_kubernetes_cluster_id | TRUE     | string  |                            | "kubernetes-cluster-id"   | Kubernetes cluster ID to use                                   |
| vsphere_cloud_controller_image_tag     | TRUE     | string  |                            | "latest"                  | Kubernetes cluster ID to use                                   |
| vsphere_syncer_image_tag               | TRUE     | string  |                            | "v1.0.2"                  | Syncer image tag to use                                        |
| vsphere_csi_attacher_image_tag         | TRUE     | string  |                            | "v1.1.1"                  | CSI attacher image tag to use                                  |
| vsphere_csi_controller                 | TRUE     | string  |                            | "v1.0.2"                  | CSI controller image tag to use                                |
| vsphere_csi_liveness_probe_image_tag   | TRUE     | string  |                            | "v1.1.0"                  | CSI liveness probe image tag to use                            |
| vsphere_csi_provisioner_image_tag      | TRUE     | string  |                            | "v1.2.2"                  | CSI provisioner image tag to use                               |
| vsphere_csi_controller_replicas        | TRUE     | integer |                            | 1                         | Number of pods Kubernetes should deploy for the CSI controller |

## More info

For further information about the vSphere CSI Driver, you can refer to the official [vSphere Cloud Provider documentation](https://cloud-provider-vsphere.sigs.k8s.io/container_storage_interface.html).
