# Azure

To deploy Kubernetes on [Azure](https://azure.microsoft.com) uncomment the
`cloud_provider` option in `group_vars/all.yml` and set it to `'azure'`.

All your instances are required to run in a resource group and a routing table
has to be attached to the subnet your instances are in.

Not all features are supported yet though, for a list of the current status have
a look [here](https://github.com/colemickens/azure-kubernetes-status).

### Parameters
Before creating the instances you must first set the `azure_` variables in the
`group_vars/all.yml` file.

All of the values can be retrieved using the azure cli tool which can be
downloaded here: https://docs.microsoft.com/en-gb/azure/xplat-cli-install

After installation you have to run `az login` to get access to your account.


#### azure\_tenant\_id + azure\_subscription\_id
Get your tenant and subscription IDs:

```bash
> az account show
{
  "id": "<SUBSCRIPTION_ID>",
  "tenantId": "<TENANT_ID>",
  ...
}
```

#### azure\_location
The region your instances are located, can be something like `westeurope` or
`westcentralus`. A full list of region names can be retrieved via:

```bash
> az account list-locations
```

#### azure\_resource\_group
The name of the resource group your instances are in can be retrieved via:

```bash
> az group list
```

#### azure\_vnet\_name
The name of the virtual network your instances are in can be retrieved via 

```bash
> az network vnet list
```

#### azure\_subnet\_name
The name of the subnet your instances are in can be retrieved via:

```bash
> az network vnet subnet list --resource-group <RESOURCE_GROUP> --vnet-name <VNET_NAME>
```

#### azure\_security\_group\_name
The name of the network security group your instances are in can be retrieved via:

```bash
> az network nsg list
```

#### azure\_aad\_client\_id + azure\_aad\_client\_secret
You can generate your own client secret, but to get your client ID (also called
appId), you'll need to create your Azure AD application as follows:

```bash
# Choose your own values for ${YOUR_APP_NAME}, ${YOUR_APP_IDENTIFIER_URI},
# ${YOUR_APP_HOMEPAGE} and ${YOUR_APP_PASSWORD}, where
# ${YOUR_APP_IDENTIFIER_URI} could be something like "http://kubernetes"
> az ad app create \
      --display-name ${YOUR_APP_NAME} \
      --identifier-uris ${YOUR_APP_IDENTIFIER_URI} \
      --homepage ${YOUR_APP_HOMEPAGE} \
      --password ${YOUR_APP_PASSWORD}
{
    ...
    "appId": "<APP_ID>",
    ...
}
```

#### Role Setup
Finally, you will need to create a Service Principal for the newly created
application, and then assign the `Reader` role to that SP.

```bash
# 1. Take note of the "appId" parameter above, and create a Service Principal
#    for the application:
> az ad sp create --id ${APP_ID}
{
    ...
    "objectId": "<SP_OBJECT_ID>",
    ...
}

# 2. Create a role assignment:
> az role assignment create \
    --assignee-object-id ${SP_OBJECT_ID} \
    --role Reader \
    --scope "/subscriptions/${SUBSCRIPTION_ID}"
{
    ...
}
```

## Provisioning Azure with Resource Group Templates
You'll find Resource Group Templates and scripts to provision the required
infrastructure to Azure in [*contrib/azurerm*](../contrib/azurerm/README.md)

