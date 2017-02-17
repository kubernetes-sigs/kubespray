Azure
===============

To deploy Kubernetes on [Azure](https://azure.microsoft.com) uncomment the `cloud_provider` option in `group_vars/all.yml` and set it to `'azure'`.

All your instances are required to run in a resource group and a routing table has to be attached to the subnet your instances are in.

Not all features are supported yet though, for a list of the current status have a look [here](https://github.com/colemickens/azure-kubernetes-status)

### Parameters

Before creating the instances you must first set the `azure_` variables in the `group_vars/all.yml` file.

All of the values can be retrieved using the azure cli tool which can be downloaded here: https://docs.microsoft.com/en-gb/azure/xplat-cli-install
After installation you have to run `azure login` to get access to your account.


#### azure\_tenant\_id + azure\_subscription\_id
run `azure account show` to retrieve your subscription id and tenant id:
`azure_tenant_id` -> Tenant ID field
`azure_subscription_id` -> ID field


#### azure\_location
The region your instances are located, can be something like `westeurope` or `westcentralus`. A full list of region names can be retrieved via `azure location list`


#### azure\_resource\_group
The name of the resource group your instances are in, can be retrieved via `azure group list`

#### azure\_vnet\_name
The name of the virtual network your instances are in, can be retrieved via `azure network vnet list`

#### azure\_subnet\_name
The name of the subnet your instances are in, can be retrieved via `azure network vnet subnet list RESOURCE_GROUP VNET_NAME`

#### azure\_security\_group\_name
The name of the network security group your instances are in, can be retrieved via `azure network nsg list`

#### azure\_aad\_client\_id + azure\_aad\_client\_secret
These will have to be generated first:
- Create an Azure AD Application with:
`azure ad app create --name kubernetes --identifier-uris http://kubernetes --home-page http://example.com --password CLIENT_SECRET` 
The name, identifier-uri, home-page and the password can be choosen
Note the AppId in the output.
- Create Service principal for the application with:
`azure ad sp create --applicationId AppId`
This is the AppId from the last command
- Create the role assignment with:
`azure role assignment create --spn http://kubernetes -o "Owner" -c /subscriptions/SUBSCRIPTION_ID`

azure\_aad\_client\_id must be set to the AppId, azure\_aad\_client\_secret is your choosen secret.

## Provisioning Azure with Resource Group Templates

You'll find Resource Group Templates and scripts to provision the required infrastructure to Azure in [*contrib/azurerm*](../contrib/azurerm/README.md)
