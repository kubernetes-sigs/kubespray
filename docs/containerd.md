# containerd

[containerd] An industry-standard container runtime with an emphasis on simplicity, robustness and portability
Kubespray supports basic functionality for using containerd as the default container runtime in a cluster.

_To use the containerd container runtime set the following variables:_

## k8s-cluster.yml

```yaml
container_manager: containerd
```

## etcd.yml

```yaml
etcd_deployment_type: host
```

## Containerd config

Example: define registry mirror for docker hub, and an insecure internal registry:

```yaml
containerd_config:
  grpc:
    max_recv_message_size: 16777216
    max_send_message_size: 16777216
  debug:
    level: ""
  registries:
    "docker.io":
      - "https://mirror.gcr.io"
      - "https://registry-1.docker.io"
    "registry.internal":
      endpoint:
        - registry.internal
      # ca_file: "ca.pem"
      # cert_file: "cert.pem"
      # key_file: "key.pem"
      insecure_skip_verify: true
      # username: ""
      # password: ""
      # auth: ""
      # identitytoken: ""
```

All available configuration items are documented [here](https://github.com/containerd/containerd/blob/master/docs/cri/registry.md).

[containerd]: https://containerd.io/
