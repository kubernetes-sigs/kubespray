# Cloudstack CSI Driver

Cloudstack CSI driver allows you to provision volumes over a Cloudstack deployment.

## Prerequisites

Official documentation with prerequisites [official guide](https://github.com/apalia/cloudstack-csi-driver#requirements).

## Kubespray configuration

To enable Cloudstack CSI driver, uncomment the `cloudstack_csi_enabled` option in `group_vars/all/cloudstack.yml` and set it to `true`.

To set the number of replicas for the Cloudstack CSI controller, you can change `cloudstack_csi_controller_replicas` option in `group_vars/all/Cloudstack.yml`.

## Parameters

| Variable                            | Required | Type       | Choices    | Default | Comment                            |
|-------------------------------------|----------|------------|------------|---------|------------------------------------|
| cloudstack_csi_enabled              | TRUE     | Boolean    | True/False | False   | Enabled Cloudstack CSI driver      |
| cloudstack_cloud_config_api_url     | TRUE     | string     |            |         | URL of the Cloudstack API endpoint |
| cloudstack_cloud_config_api_key     | TRUE     | string     |            |         | Cloudstack API key                 |
| cloudstack_cloud_config_secret_key  | TRUE     | string     |            |         | Cloudstack Secret Key              |
| cloudstack_sc_diks_offering_id      | TRUE     | string     |            |         | Disk Offering ID for storage class |
| cloudstack_csi_controller_replicas  | TRUE     | Integer    |            |  1      | Controller replica count           |
