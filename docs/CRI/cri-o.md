# CRI-O

[CRI-O] is a lightweight container runtime for Kubernetes.
Kubespray supports basic functionality for using CRI-O as the default container runtime in a cluster.

* Kubernetes supports CRI-O on v1.11.1 or later.
* etcd: configure either kubeadm managed etcd or host deployment

_To use the CRI-O container runtime set the following variables:_

## all/all.yml

```yaml
download_container: false
skip_downloads: false
etcd_deployment_type: host # optionally kubeadm
```

## k8s_cluster/k8s_cluster.yml

```yaml
container_manager: crio
```

## all/crio.yml

Enable docker hub registry mirrors

```yaml
crio_registries:
  - prefix: docker.io
    insecure: false
    blocked: false
    location: docker.io
    unqualified: true
    mirrors:
      - location: 192.168.100.100:5000
        insecure: true
      - location: mirror.gcr.io
        insecure: false
```

[CRI-O]: https://cri-o.io/

The following is a method to enable insecure registries.

```yaml
crio_insecure_registries:
  - 10.0.0.2:5000
```

And you can config authentication for these registries after `crio_insecure_registries`.

```yaml
crio_registry_auth:
  - registry: 10.0.0.2:5000
    username: user
    password: pass
```

### Unqualified (short) image names

CRI-O refuses to pull unqualified image names, such as `busybox`,
unless a registry is listed in `unqualified-search-registries`. Kubespray renders
that list from the entries of `crio_registries` flagged with `unqualified: true`,
so the default configuration above resolves short names against `docker.io`,
matching the behaviour of the containerd runtime.

Short names are commonly used by the manifests of the addons that Kubespray
installs from upstream (the local-path-provisioner helper pod is one example,
its image is `busybox`). If the addon pods stay in `ErrImagePull`/`ImagePullBackOff`
with an error such as:

```text
short-name "busybox" did not resolve to an alias and no
unqualified-search registries are defined in "/etc/containers/registries.conf.d/01-unqualified.conf"
```

then no registry is flagged as `unqualified`. Add one, for example:

```yaml
crio_registries:
  - prefix: docker.io
    insecure: false
    blocked: false
    location: docker.io
    unqualified: true
```

To disallow unqualified image names, opt out explicitly:

```yaml
crio_registries: []
```

## Note about user namespaces

CRI-O has support for user namespaces. This feature is optional and can be enabled by setting the following two variables.

```yaml
crio_runtimes:
  - name: runc
    path: /usr/bin/runc
    type: oci
    root: /run/runc
    allowed_annotations:
    - "io.kubernetes.cri-o.userns-mode"

crio_remap_enable: true
```

The `allowed_annotations` configures `crio.conf` accordingly.

The `crio_remap_enable` configures the `/etc/subuid` and `/etc/subgid` files to add an entry for the **containers** user.
By default, 16M uids and gids are reserved for user namespaces (256 pods * 65536 uids/gids) at the end of the uid/gid space.

The `crio_default_capabilities` configure the default containers capabilities for the crio.
Defaults capabilities are:

```yaml
crio_default_capabilities:
  - CHOWN
  - DAC_OVERRIDE
  - FSETID
  - FOWNER
  - SETGID
  - SETUID
  - SETPCAP
  - NET_BIND_SERVICE
  - KILL
```

You can add MKNOD to the list for a rancher deployment

## Optional : NRI

[Node Resource Interface](https://github.com/containerd/nri) (NRI) is disabled by default for the CRI-O. If you
are using CRI-O version v1.26.0 or above, then you can enable it with the
following configuration:

```yaml
nri_enabled: true
```
