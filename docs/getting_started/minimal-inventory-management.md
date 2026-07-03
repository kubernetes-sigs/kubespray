# Minimal Inventory Management

## Overview

When managing Kubespray configurations, it is common to copy the entire `inventory/sample` directory into your version control system. However, this approach stores hundreds of default files that are rarely modified, wasting storage space and making it difficult to identify which settings differ from defaults.

This guide shows how to manage Kubespray configuration with minimal files by storing only the customizations needed for your cluster.

## The Problem

The default approach requires copying the entire `inventory/sample` directory structure:

```
./group_vars/k8s_cluster/
  k8s-cluster.yml
  addons.yml
  k8s-net-flannel.yml
  k8s-net-calico.yml
  (and many more...)
./group_vars/all/
  all.yml
  aws.yml
  azure.yml
  gcp.yml
  (and many more...)
./inventory.ini
```

Most clusters only change a few parameters, such as:

```yaml
# In group_vars/k8s_cluster/k8s-cluster.yml
cluster_name: mycluster.example.com
supplementary_addresses_in_ssl_keys:
  - node1.mycluster.example.com
  - node2.mycluster.example.com

# In group_vars/k8s_cluster/addons.yml
helm_enabled: true
metrics_server_enabled: true
```

Storing hundreds of unchanged files makes it difficult to see what was actually customized for your cluster.

## The Solution

Create a minimal inventory containing only the host definitions and customizations. This approach stores only what differs from Kubespray defaults.

### Directory Structure

Create a minimal inventory directory with just two files:

```
mycluster-config/
  hosts.yaml
  group_vars/
    all.yaml
```

### hosts.yaml

Define your cluster hosts and groups using YAML format:

```yaml
all:
  vars:
    ansible_connection: ssh
    ansible_user: root
  hosts:
    node1:
      ansible_host: 10.0.0.1
    node2:
      ansible_host: 10.0.0.2
    node3:
      ansible_host: 10.0.0.3
  children:
    kube_control_plane:
      hosts:
        node1:
    kube_node:
      hosts:
        node2:
        node3:
    etcd:
      hosts:
        node1:
```

### group_vars/all.yaml

Include all variables that differ from Kubespray defaults in a single file:

```yaml
---
# Network settings
bootstrap_os: ubuntu

# Container runtime (if not using default)
container_manager: containerd

# Custom DNS or other cluster-wide settings
upstream_dns_servers:
  - 8.8.8.8
  - 8.8.4.4

# Cluster name and SSL settings
cluster_name: mycluster.example.com
supplementary_addresses_in_ssl_keys:
  - mycluster.example.com
  - node1.mycluster.example.com
  - node2.mycluster.example.com
  - node3.mycluster.example.com

# Network ranges
kube_service_addresses: 10.233.0.0/18
kube_pods_subnet: 10.233.64.0/18

# Enable needed addons
helm_enabled: true
metrics_server_enabled: true
```

> **Note:** The `k8s_cluster` group is automatically computed by Kubespray from `kube_control_plane` and `kube_node` groups, so you don't need to define it manually.

## Using the Minimal Configuration

To deploy a cluster using your minimal configuration:

1. Clone Kubespray to your local machine or deployment host
2. Place your minimal inventory files in `inventory/mycluster/`
3. Run the cluster.yml playbook as normal:

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.yaml cluster.yml -b -v \
  --private-key=~/.ssh/private_key
```

Kubespray will merge your overrides with the default values from `inventory/sample`.

## Benefits

Storing only customizations offers several advantages:

- Smaller git repository footprint
- Easier identification of cluster-specific settings
- Simpler version control and history tracking
- Reduced clutter when reviewing configuration changes
- Easier to compare configurations across multiple clusters

## Reference Implementation

For a complete example of minimal inventory management, see the reference repository at https://github.com/Murz-K8s/kubespray-inventory-base

## See Also

- [Building your own inventory](/docs/getting_started/getting-started.md#building-your-own-inventory)
- [Inventory documentation](/docs/ansible/inventory.md)
- [Ansible documentation on inventory](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html)
