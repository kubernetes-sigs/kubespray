# Docker support

The docker runtime is supported by kubespray and while the `dockershim` is deprecated to be removed in kubernetes 1.24+ there are alternative ways to use docker such as through the [cri-dockerd](https://github.com/Mirantis/cri-dockerd) project supported by Mirantis.

Using the docker container manager:

```yaml
container_manager: docker
```

*Note:* `cri-dockerd` has replaced `dockershim` across supported kubernetes version in kubespray 2.20.

Enabling the `overlay2` graph driver:

```yaml
docker_storage_options: -s overlay2
```

Enabling `docker_container_storage_setup`, it will configure devicemapper driver on Centos7 or RedHat7.
Deployers must be define a disk path for `docker_container_storage_setup_devs`, otherwise docker-storage-setup will be executed incorrectly.

```yaml
docker_container_storage_setup: true
docker_container_storage_setup_devs: /dev/vdb
```

Changing the Docker cgroup driver (native.cgroupdriver); valid options are `systemd` or `cgroupfs`, default is `systemd`:

```yaml
docker_cgroup_driver: systemd
```

If you have more than 3 nameservers kubespray will only use the first 3 else it will fail. Set the `docker_dns_servers_strict` to `false` to prevent deployment failure.

```yaml
docker_dns_servers_strict: false
```

Set the path used to store Docker data:

```yaml
docker_daemon_graph: "/var/lib/docker"
```

Changing the docker daemon iptables support:

```yaml
docker_iptables_enabled: "false"
```

Docker log options:

```yaml
# Rotate container stderr/stdout logs at 50m and keep last 5
docker_log_opts: "--log-opt max-size=50m --log-opt max-file=5"
```

Change the docker `bin_dir`, this should not be changed unless you use a custom docker package:

```yaml
docker_bin_dir: "/usr/bin"
```

To keep docker packages after installation; speeds up repeated ansible provisioning runs when '1'.
kubespray deletes the docker package on each run, so caching the package makes sense:

```yaml
docker_rpm_keepcache: 1
```

Allowing insecure-registry access to self hosted registries. Can be ipaddress and domain_name.

```yaml
## example define 172.19.16.11 or mirror.registry.io
docker_insecure_registries:
  - mirror.registry.io
  - 172.19.16.11
```

Adding other registry, i.e. China registry mirror:

```yaml
docker_registry_mirrors:
  - https://registry.docker-cn.com
  - https://mirror.aliyuncs.com
```

Overriding default system MountFlags value. This option takes a mount propagation flag: `shared`, `slave` or `private`, which control whether mounts in the file system namespace set up for docker will receive or propagate mounts and unmounts. Leave empty for system default:

```yaml
docker_mount_flags:
```

Adding extra options to pass to the docker daemon:

```yaml
## This string should be exactly as you wish it to appear.
docker_options: ""
```

For Debian based distributions, set the path to store the GPG key to avoid using the default one used in `apt_key` module (e.g. /etc/apt/trusted.gpg)

```yaml
docker_repo_key_keyring: /etc/apt/trusted.gpg.d/docker.gpg
```
