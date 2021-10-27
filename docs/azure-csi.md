# Azure Disk CSI Driver

The Azure Disk CSI driver allows you to provision volumes for pods with a Kubernetes deployment over Azure Cloud. The CSI driver replaces to volume provisioning done by the in-tree azure cloud provider which is deprecated.

This documentation is an updated version of the in-tree Azure cloud provider documentation (azure.md).

To deploy Azure Disk CSI driver, uncomment the `azure_csi_enabled` option in `group_vars/all/azure.yml` and set it to `true`.

## Azure Disk CSI Storage Class

If you want to deploy the Azure Disk storage class to provision volumes dynamically, you should set `persistent_volumes_enabled` in `group_vars/k8s_cluster/k8s_cluster.yml` to `true`.

## Parameters

Before creating the instances you must first set the `azure_csi_` variables in the `group_vars/all.yml` file.

All of the values can be retrieved using the azure cli tool which can be downloaded here: <https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest>

After installation you have to run `az login` to get access to your account.

### azure\_csi\_tenant\_id + azure\_csi\_subscription\_id

Run `az account show` to retrieve your subscription id and tenant id:
`azure_csi_tenant_id` -> tenantId field
`azure_csi_subscription_id` -> id field

### azure\_csi\_location

The region your instances are located in, it can be something like `francecentral` or `norwayeast`. A full list of region names can be retrieved via `az account list-locations`

### azure\_csi\_resource\_group

The name of the resource group your instances are in, a list of your resource groups can be retrieved via `az group list`

Or you can do `az vm list | grep resourceGroup` and get the resource group corresponding to the VMs of your cluster.

The resource group name is not case sensitive.

### azure\_csi\_vnet\_name

The name of the virtual network your instances are in, can be retrieved via `az network vnet list`

### azure\_csi\_vnet\_resource\_group

The name of the resource group your vnet is in, can be retrieved via `az network vnet list | grep resourceGroup` and get the resource group corresponding to the vnet of your cluster.

### azure\_csi\_subnet\_name

The name of the subnet your instances are in, can be retrieved via `az network vnet subnet list --resource-group RESOURCE_GROUP --vnet-name VNET_NAME`

### azure\_csi\_security\_group\_name

The name of the network security group your instances are in, can be retrieved via `az network nsg list`

### azure\_csi\_aad\_client\_id + azure\_csi\_aad\_client\_secret

These will have to be generated first:

- Create an Azure AD Application with:
`az ad app create --display-name kubespray --identifier-uris http://kubespray --homepage http://kubespray.com --password CLIENT_SECRET`

Display name, identifier-uri, homepage and the password can be chosen

Note the AppId in the output.

- Create Service principal for the application with:
`az ad sp create --id AppId`

This is the AppId from the last command

- Create the role assignment with:
`az role assignment create --role "Owner" --assignee http://kubespray --subscription SUBSCRIPTION_ID`

azure\_csi\_aad\_client\_id must be set to the AppId, azure\_csi\_aad\_client\_secret is your chosen secret.

### azure\_csi\_use\_instance\_metadata

Use instance metadata service where possible. Boolean value.

## Test the Azure Disk CSI driver

To test the dynamic provisioning using Azure CSI driver, make sure to have the storage class deployed (through persistent volumes), and apply the following manifest:

```yml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-azuredisk
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: disk.csi.azure.com
---
kind: Pod
apiVersion: v1
metadata:
  name: nginx-azuredisk
spec:
  nodeSelector:
    kubernetes.io/os: linux
  containers:
    - image: nginx
      name: nginx-azuredisk
      command:
        - "/bin/sh"
        - "-c"
        - while true; do echo $(date) >> /mnt/azuredisk/outfile; sleep 1; done
      volumeMounts:
        - name: azuredisk
          mountPath: "/mnt/azuredisk"
  volumes:
    - name: azuredisk
      persistentVolumeClaim:
        claimName: pvc-azuredisk
```
