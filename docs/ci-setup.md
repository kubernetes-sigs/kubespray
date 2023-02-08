# CI Setup

## Pipeline

1. build: build a docker image to be used in the pipeline
2. unit-tests: fast jobs for fast feedback (linting, etc...)
3. deploy-part1: small number of jobs to test if the PR works with default settings
4. deploy-part2: slow jobs testing different platforms, OS, settings, CNI, etc...
5. deploy-part3: very slow jobs (upgrades, etc...)

## Runners

Kubespray has 3 types of GitLab runners:

- packet runners: used for E2E jobs (usually long), running on Equinix Metal (ex-packet), on kubevirt managed VMs
- light runners: used for short lived jobs, running on Equinix Metal (ex-packet), as managed pods
- auto scaling runners (managed via docker-machine on Equinix Metal): used for on-demand resources, see [GitLab docs](https://docs.gitlab.com/runner/configuration/autoscale.html) for more info

## Vagrant

Vagrant jobs are using the [quay.io/kubespray/vagrant](/test-infra/vagrant-docker/Dockerfile) docker image with `/var/run/libvirt/libvirt-sock` exposed from the host, allowing the container to boot VMs on the host.

## CI Variables

In CI we have a set of overrides we use to ensure greater success of our CI jobs and avoid throttling by various APIs we depend on. See:

- [Docker mirrors](/tests/common/_docker_hub_registry_mirror.yml)
- [Test settings](/tests/common/_kubespray_test_settings.yml)

## CI Environment

The CI packet and light runners are deployed on a kubernetes cluster on Equinix Metal. The cluster is deployed with kubespray itself and maintained by the kubespray maintainers.

The following files are used for that inventory:

### cluster.tfvars

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
facility = "am6"

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

containerd_registries:
  "docker.io":
    - "https://mirror.gcr.io"
    - "https://registry-1.docker.io"

containerd_max_container_log_line_size: -1

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

### /root/nscleanup.sh

```bash
#!/bin/bash

kubectl=/usr/local/bin/kubectl

$kubectl get ns | grep -P "(\d.+-\d.+)" | awk 'match($3,/[0-9]+d/) {print $1}' | xargs -r $kubectl delete ns
$kubectl get ns | grep -P "(\d.+-\d.+)" | awk 'match($3,/[3-9]+h/) {print $1}' | xargs -r $kubectl delete ns
$kubectl get ns | grep Terminating | awk '{print $1}' | xargs -i $kubectl delete vmi/instance-1 vmi/instance-0 vmi/instance-2 -n {} --force --grace-period=0 &
```

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
