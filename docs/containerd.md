# containerd

[containerd] An industry-standard container runtime with an emphasis on simplicity, robustness and portability
Kubespray supports basic functionality for using containerd as the default container runtime in a cluster.

_To use the containerd container runtime set the following variables:_

## k8s_cluster.yml

When kube_node contains etcd, you define your etcd cluster to be as well schedulable for Kubernetes workloads. Thus containerd and dockerd can not run at same time, must be set to bellow for running etcd cluster with only containerd.

```yaml
container_manager: containerd
```

## etcd.yml

```yaml
etcd_deployment_type: host
```

## Containerd config

Example: define registry mirror for docker hub

```yaml
containerd_registries:
  "docker.io":
    - "https://mirror.gcr.io"
    - "https://registry-1.docker.io"
```

`containerd_registries` is ignored for pulling images when `image_command_tool=nerdctl`
(the default for `container_manager=containerd`). Use `crictl` instead, it supports
`containerd_registries` but lacks proper multi-arch support (see
[#8375](https://github.com/kubernetes-sigs/kubespray/issues/8375)):

```yaml
image_command_tool: crictl
```

### Containerd Runtimes

Containerd supports multiple runtime configurations that can be used with
[RuntimeClass] Kubernetes feature. See [runtime classes in containerd] for the
details of containerd configuration.

In kubespray, the default runtime name is "runc", and it can be configured with the `containerd_runc_runtime` dictionary:

```yaml
containerd_runc_runtime:
  name: runc
  type: "io.containerd.runc.v2"
  engine: ""
  root: ""
  options:
    systemdCgroup: "false"
    binaryName: /usr/local/bin/my-runc
  base_runtime_spec: cri-base.json
```

Further runtimes can be configured with `containerd_additional_runtimes`, which
is a list of such dictionaries.

Default runtime can be changed by setting `containerd_default_runtime`.

#### base_runtime_spec

`base_runtime_spec` key in a runtime dictionary can be used to explicitly
specify a runtime spec json file. We ship the default one which is generated
with `ctr oci spec > /etc/containerd/cri-base.json`. It will be used if you set
`base_runtime_spec: cri-base.json`. The main advantage of doing so is the presence of
`rlimits` section in this configuration, which will restrict the maximum number
of file descriptors(open files) per container to 1024.

You can tune many more [settings][runtime-spec] by supplying your own file name and content with `containerd_base_runtime_specs`:

```yaml
containerd_base_runtime_specs:
  cri-spec-custom.json: |
    {
      "ociVersion": "1.0.2-dev",
      "process": {
        "user": {
          "uid": 0,
    ...
```

The files in this dict will be placed in containerd config directory,
`/etc/containerd` by default. The files can then be referenced by filename in a
runtime:

```yaml
containerd_runc_runtime:
  name: runc
  base_runtime_spec: cri-spec-custom.json
  ...
```

[containerd]: https://containerd.io/
[RuntimeClass]: https://kubernetes.io/docs/concepts/containers/runtime-class/
[runtime classes in containerd]: https://github.com/containerd/containerd/blob/main/docs/cri/config.md#runtime-classes
[runtime-spec]: https://github.com/opencontainers/runtime-spec
