# Kata Containers

[Kata Containers](https://katacontainers.io) is a secure container runtime with lightweight virtual machines that supports multiple hypervisor solutions.

## Hypervisors

_Qemu_ is the only hypervisor supported by Kubespray.

## Installation

To enable Kata Containers, set the following variables:

**k8s-cluster.yml**:

```yaml
container_manager: containerd
kata_containers_enabled: true
```

**etcd.yml**:

```yaml
etcd_deployment_type: host
```

## Usage

By default, runc is used for pods.
Kubespray generates the runtimeClass kata-qemu, and it is necessary to specify it as
the runtimeClassName of a pod spec to use Kata Containers:

```shell
$ kubectl get runtimeclass
NAME        HANDLER     AGE
kata-qemu   kata-qemu   3m34s
$
$ cat nginx.yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  runtimeClassName: kata-qemu
  containers:
  - name: nginx
    image: nginx:1.14.2
$
$ kubectl apply -f nginx.yaml
```

## Configuration

### Recommended : Pod Overhead

[Pod Overhead](https://kubernetes.io/docs/concepts/configuration/pod-overhead/) is a feature for accounting for the resources consumed by the Runtime Class used by the Pod.

When this feature is enabled, Kubernetes will count the fixed amount of CPU and memory set in the configuration as used by the virtual machine and not by the containers running in the Pod.

Pod Overhead is mandatory if you run Pods with Kata Containers that use [resources limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#requests-and-limits).

**Set cgroup driver**:

To enable Pod Overhead feature you have to configure Kubelet with the appropriate cgroup driver, using the following configuration:

`cgroupfs` works best:

```yaml
kubelet_cgroup_driver: cgroupfs
```

... but when using `cgroups v2` (see <https://www.redhat.com/en/blog/world-domination-cgroups-rhel-8-welcome-cgroups-v2>) you can use systemd as well:

```yaml
kubelet_cgroup_driver: systemd
```

**Qemu hypervisor configuration**:

The configuration for the Qemu hypervisor uses the following values:

```yaml
kata_containers_qemu_overhead: true
kata_containers_qemu_overhead_fixed_cpu: 10m
kata_containers_qemu_overhead_fixed_memory: 290Mi
```

### Optional : Select Kata Containers version

Optionally you can select the Kata Containers release version to be installed. The available releases are published in [GitHub](https://github.com/kata-containers/kata-containers/releases).

```yaml
kata_containers_version: 2.2.2
```

### Optional : Debug

Debug is disabled by default for all the components of Kata Containers. You can change this behaviour with the following configuration:

```yaml
kata_containers_qemu_debug: 'false'
```
