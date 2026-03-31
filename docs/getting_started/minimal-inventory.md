# Minimal Inventory Guide

This document describes best practices for managing Kubespray custom configurations
in a separate git repository with minimal files.

## Why a Minimal Inventory

Many tutorials recommend copying the entire `inventory/sample` directory to
`inventory/myclustername` and then modifying options directly in those files.
While this works well for getting started, it results in:

- A large number of files in your custom git repository
- Difficulty distinguishing which settings differ from Kubespray defaults
- Increased maintenance burden when Kubespray updates sample files

A better approach is to keep only the files that contain your custom
configuration and reference Kubespray as a git submodule. This makes it easy
to track what you have customized and to update Kubespray independently.

## Minimal Inventory Structure

For most clusters, you only need these two files:

```
your-repo/
├── inventory/
│   └── mycluster/
│       ├── hosts.yaml          # Cluster topology (nodes and groups)
│       └── group_vars/
│           └── all.yaml        # Custom configuration overrides
├── kubespray                   # Submodule pointing to Kubespray
└── .gitmodules
```

## Hosts File

Create `inventory/mycluster/hosts.yaml` to define your cluster topology.

### Single-node cluster example

```yaml
all:
  hosts:
    node1:
      ansible_host: 192.168.1.10
      # Internal IP for the node (optional)
      # ip: 10.0.0.2
  children:
    kube_control_plane:
      hosts:
        node1:
    kube_node:
      hosts:
        node1:
    etcd:
      hosts:
        node1:
    k8s_cluster:
      children:
        kube_control_plane:
        kube_node:
```

### Multi-node HA cluster example

```yaml
all:
  vars:
    ansible_user: deploy
    # ansible_ssh_private_key_file: ~/.ssh/id_rsa
  hosts:
    controller1:
      ansible_host: 192.168.1.10
    controller2:
      ansible_host: 192.168.1.11
    controller3:
      ansible_host: 192.168.1.12
    worker1:
      ansible_host: 192.168.1.20
    worker2:
      ansible_host: 192.168.1.21
    worker3:
      ansible_host: 192.168.1.22
  children:
    kube_control_plane:
      hosts:
        controller1:
        controller2:
        controller3:
    kube_node:
      hosts:
        worker1:
        worker2:
        worker3:
    etcd:
      hosts:
        controller1:
        controller2:
        controller3:
    k8s_cluster:
      children:
        kube_control_plane:
        kube_node:
```

> **Note:** `etcd` is defined as a child of `kube_control_plane` for a
"stacked" etcd topology. For external etcd, create a separate `[etcd]` group
with its own hosts.

## Group Variables File

Create `inventory/mycluster/group_vars/all.yaml` with only the settings that
differ from Kubespray defaults:

```yaml
# Cluster identity
cluster_name: mycluster.example.com

# SSL certificate SAN entries
supplementary_addresses_in_ssl_keys:
  - controller1.example.com
  - controller2.example.com
  - controller3.example.com

# Enable optional components
helm_enabled: true
metrics_server_enabled: true
metrics_server_kubelet_insecure_tls: true
krew_enabled: true
```

You only need to list variables that you want to override. Kubespray has
sensible defaults for most settings. Check
`roles/kubespray_defaults/defaults/main/` for the complete list of default
values.

## Setting Up Kubespray as a Git Submodule

This workflow keeps Kubespray as a dependency rather than copying all files:

1. **Initialize your repository:**

   ```bash
   git init
   git remote add origin <your-repo-url>
   ```

2. **Add Kubespray as a submodule:**

   ```bash
   git submodule add https://github.com/kubernetes-sigs/kubespray.git kubespray
   ```

3. **Create your inventory structure:**

   ```bash
   mkdir -p inventory/mycluster/group_vars
   ```

4. **Create `hosts.yaml` and `group_vars/all.yaml`** as described above.

5. **Commit your changes:**

   ```bash
   git add .gitmodules kubespray inventory/
   git commit -m "Add minimal Kubespray inventory"
   ```

## Running Kubespray

Navigate to the Kubespray directory and run the playbook:

```bash
cd kubespray
ansible-playbook -i ../inventory/mycluster cluster.yml -b -v
  --private-key=~/.ssh/id_rsa
```

Or set the `ANSIBLE_INVENTORY` environment variable:

```bash
export ANSIBLE_INVENTORY=../inventory/mycluster
cd kubespray
ansible-playbook cluster.yml -b -v --private-key=~/.ssh/id_rsa
```

## Organizing Group-Specific Variables

As your configuration grows, you may want to organize variables by group:

```
inventory/mycluster/
├── hosts.yaml
└── group_vars/
    ├── all.yaml                    # Global settings
    ├── kube_control_plane.yaml     # Control plane only
    ├── kube_node.yaml              # Worker nodes only
    └── etcd.yaml                   # etcd nodes only
```

Example `group_vars/kube_control_plane.yaml`:

```yaml
supplementary_addresses_in_ssl_keys:
  - controller1.example.com
  - controller2.example.com
  - controller3.example.com
```

This approach keeps your configuration organized and makes it clear which
settings apply to which nodes.

## Using INI Format Instead of YAML

If you prefer the INI format, you can use `hosts.ini`:

```ini
[kube_control_plane]
controller1 ansible_host=192.168.1.10
controller2 ansible_host=192.168.1.11
controller3 ansible_host=192.168.1.12

[kube_node]
worker1 ansible_host=192.168.1.20
worker2 ansible_host=192.168.1.21
worker3 ansible_host=192.168.1.22

[etcd:children]
kube_control_plane

[k8s_cluster:children]
kube_control_plane
kube_node
```

## Migrating from inventory/sample

If you have an existing cluster based on `inventory/sample`, you can migrate
to a minimal inventory:

1. Create a new inventory directory
2. Copy your `hosts.yaml` (or create a new one from the examples above)
3. Review your existing `group_vars` and copy only the non-default settings
4. Test with the new inventory before removing the old files