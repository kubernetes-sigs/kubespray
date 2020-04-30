# Azure

To deploy Kubernetes on [Azure](https://azure.microsoft.com) uncomment the `cloud_provider` option in `group_vars/all/all.yml` and set it to `'azure'`.

All your instances are required to run in a resource group and a routing table has to be attached to the subnet your instances are in.

Not all features are supported yet though, for a list of the current status have a look [here](https://github.com/Azure/AKS)

## Parameters

Before creating the instances you must first set the `azure_` variables in the `group_vars/all/all.yml` file.

All of the values can be retrieved using the azure cli tool which can be downloaded here: <https://docs.microsoft.com/en-gb/azure/xplat-cli-install>
After installation you have to run `az login` to get access to your account.

### azure\_tenant\_id + azure\_subscription\_id

run `az account show` to retrieve your subscription id and tenant id:
`azure_tenant_id` -> Tenant ID field
`azure_subscription_id` -> ID field

### azure\_location

The region your instances are located, can be something like `westeurope` or `westcentralus`. A full list of region names can be retrieved via `az account list-locations`

### azure\_resource\_group

The name of the resource group your instances are in, can be retrieved via `az group list`

### azure\_vmtype

The type of the vm. Supported values are `standard` or `vmss`. If vm is type of `Virtal Machines` then value is `standard`. If vm is part of `Virtaul Machine Scale Sets` then value is `vmss`

### azure\_vnet\_name

The name of the virtual network your instances are in, can be retrieved via `az network vnet list`

### azure\_subnet\_name

The name of the subnet your instances are in, can be retrieved via `az network vnet subnet list --resource-group RESOURCE_GROUP --vnet-name VNET_NAME`

### azure\_security\_group\_name

The name of the network security group your instances are in, can be retrieved via `az network nsg list`

### azure\_aad\_client\_id + azure\_aad\_client\_secret

These will have to be generated first:

- Create an Azure AD Application with:
`az ad app create --display-name kubernetes --identifier-uris http://kubernetes --homepage http://example.com --password CLIENT_SECRET`
display name, identifier-uri, homepage and the password can be chosen
Note the AppId in the output.
- Create Service principal for the application with:
`az ad sp create --id AppId`
This is the AppId from the last command
- Create the role assignment with:
`az role assignment create --role "Owner" --assignee http://kubernetes --subscription SUBSCRIPTION_ID`

azure\_aad\_client\_id must be set to the AppId, azure\_aad\_client\_secret is your chosen secret.

### azure\_loadbalancer\_sku

Sku of Load Balancer and Public IP. Candidate values are: basic and standard.

### azure\_exclude\_master\_from\_standard\_lb

azure\_exclude\_master\_from\_standard\_lb excludes master nodes from `standard` load balancer.

### azure\_disable\_outbound\_snat

azure\_disable\_outbound\_snat disables the outbound SNAT for public load balancer rules. It should only be set when azure\_exclude\_master\_from\_standard\_lb is `standard`.

### azure\_primary\_availability\_set\_name

(Optional) The name of the availability set that should be used as the load balancer backend .If this is set, the Azure
cloudprovider will only add nodes from that availability set to the load balancer backend pool. If this is not set, and
multiple agent pools (availability sets) are used, then the cloudprovider will try to add all nodes to a single backend
pool which is forbidden. In other words, if you use multiple agent pools (availability sets), you MUST set this field.

### azure\_use\_instance\_metadata

Use instance metadata service where possible

## Provisioning Azure with Resource Group Templates

You'll find Resource Group Templates and scripts to provision the required infrastructure to Azure in [*contrib/azurerm*](../contrib/azurerm/README.md)
