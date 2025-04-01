# CI Setup

## Pipeline

See [.gitlab-ci.yml](/.gitlab-ci.yml) and the included files for an overview.

## Runners

Kubespray has 2 types of GitLab runners, both deployed  on the Kubespray CI cluster (hosted on Oracle Cloud Infrastucture):

- pods: use the [gitlab-ci kubernetes executor](https://docs.gitlab.com/runner/executors/kubernetes/)
- vagrant: custom executor running in pods with access to the libvirt socket on the nodes

## Vagrant

Vagrant jobs are using the [quay.io/kubespray/vagrant](/test-infra/vagrant-docker/Dockerfile) docker image with `/var/run/libvirt/libvirt-sock` exposed from the host, allowing the container to boot VMs on the host.

## CI Variables

In CI we have a [set of extra vars](/test/common_vars.yml) we use to ensure greater success of our CI jobs and avoid throttling by various APIs we depend on.

## CI clusters

DISCLAIMER: The following information is not fully up to date, in particular, the CI cluster is now on Oracle Cloud Infrastcture, not Equinix.

The cluster is deployed with kubespray itself and maintained by the kubespray maintainers.

The following files are used for that inventory:

### cluster.tfvars (OBSOLETE: this section is no longer accurate)

```ini
# your Kubernetes cluster name here
cluster_name = "ci"

# Your Equinix Metal project ID. See https://metal.equinix.com/developers/docs/accounts/
equinix_metal_project_id = "_redacted_"

# The public SSH key to be uploaded into authorized_keys in bare metal Equinix Metal nodes provisioned
# leave this value blank if the public key is already setup in the Equinix Metal project
# Terraform will complain if the public key is setup in Equinix Metal
public_key_path = "~/.ssh/id_rsa.pub"

# cluster location
metro = "da"

# standalone etcds
number_of_etcd = 0

plan_etcd = "t1.small.x86"

# masters
number_of_k8s_masters = 1

number_of_k8s_masters_no_etcd = 0

plan_k8s_masters = "c3.small.x86"

plan_k8s_masters_no_etcd = "t1.small.x86"

# nodes
number_of_k8s_nodes = 1

plan_k8s_nodes = "c3.medium.x86"
```

### group_vars/all/mirrors.yml

```yaml
---
docker_registry_mirrors:
  - "https://mirror.gcr.io"

containerd_grpc_max_recv_message_size: 16777216
containerd_grpc_max_send_message_size: 16777216

containerd_registries_mirrors:
  - prefix: docker.io
    mirrors:
      - host: https://mirror.gcr.io
        capabilities: ["pull", "resolve"]
        skip_verify: false
      - host: https://registry-1.docker.io
        capabilities: ["pull", "resolve"]
        skip_verify: false

containerd_max_container_log_line_size: 16384

crio_registries_mirrors:
  - prefix: docker.io
    insecure: false
    blocked: false
    location: registry-1.docker.io
    mirrors:
      - location: mirror.gcr.io
        insecure: false

netcheck_agent_image_repo: "{{ quay_image_repo }}/kubespray/k8s-netchecker-agent"
netcheck_server_image_repo: "{{ quay_image_repo }}/kubespray/k8s-netchecker-server"

nginx_image_repo: "{{ quay_image_repo }}/kubespray/nginx"
```

### group_vars/all/settings.yml

```yaml
---
# Networking setting
kube_service_addresses: 172.30.0.0/18
kube_pods_subnet: 172.30.64.0/18
kube_network_plugin: calico
# avoid overlap with CI jobs deploying nodelocaldns
nodelocaldns_ip: 169.254.255.100

# ipip: False
calico_ipip_mode: "Never"
calico_vxlan_mode: "Never"
calico_network_backend: "bird"
calico_wireguard_enabled: True

# Cluster settings
upgrade_cluster_setup: True
force_certificate_regeneration: True

# Etcd settings
etcd_deployment_type: "host"

# Kubernetes settings
kube_controller_terminated_pod_gc_threshold: 100
kubelet_enforce_node_allocatable: pods
kubelet_preferred_address_types: 'InternalIP,ExternalIP,Hostname'
kubelet_custom_flags:
  - "--serialize-image-pulls=true"
  - "--eviction-hard=memory.available<1Gi"
  - "--eviction-soft-grace-period=memory.available=30s"
  - "--eviction-soft=memory.available<2Gi"
  - "--system-reserved cpu=100m,memory=4Gi"
  - "--eviction-minimum-reclaim=memory.available=2Gi"

# DNS settings
resolvconf_mode: none
dns_min_replicas: 1
upstream_dns_servers:
  - 1.1.1.1
  - 1.0.0.1

# Extensions
ingress_nginx_enabled: True
helm_enabled: True
cert_manager_enabled: True
metrics_server_enabled: True

# Enable ZSWAP
kubelet_fail_swap_on: False
kube_feature_gates:
  - "NodeSwap=True"
```

## Aditional files

This section documents additional files used to complete a deployment of the kubespray CI, these files sit on the control-plane node and assume a working kubernetes cluster.

### /root/path-calico.sh

```bash
#!/bin/bash

calicoctl patch felixconfig default -p '{"spec":{"allowIPIPPacketsFromWorkloads":true, "allowVXLANPacketsFromWorkloads": true}}'
```

### /root/kubevirt/kubevirt.sh

```bash
#!/bin/bash

export VERSION=$(curl -s https://api.github.com/repos/kubevirt/kubevirt/releases | grep tag_name | grep -v -- '-rc' | sort -r | head -1 | awk -F': ' '{print $2}' | sed 's/,//' | xargs)
echo $VERSION
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/${VERSION}/kubevirt-operator.yaml
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/${VERSION}/kubevirt-cr.yaml
```

### /root/kubevirt/virtctl.sh

```bash
#!/bin/bash

VERSION=$(kubectl get kubevirt.kubevirt.io/kubevirt -n kubevirt -o=jsonpath="{.status.observedKubeVirtVersion}")
ARCH=$(uname -s | tr A-Z a-z)-$(uname -m | sed 's/x86_64/amd64/') || windows-amd64.exe
echo ${ARCH}
curl -L -o virtctl https://github.com/kubevirt/kubevirt/releases/download/${VERSION}/virtctl-${VERSION}-${ARCH}
chmod +x virtctl
sudo install virtctl /usr/local/bin
```
