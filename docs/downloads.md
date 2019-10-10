Downloading files and container images
======================================

By default Kubespray downloads binaries and container images directly to
the cluster nodes:

* Each node downloads binaries and container images on its own.
* For K8s apps, pull policy is ``k8s_image_pull_policy: IfNotPresent``.
* For system managed containers, like kubelet or etcd, pull policy is ``download_always_pull: False``, which is pull if only the wanted repo and tag/sha256 digest differs from that the host has.


## Cache

Kubespray supports caching of downloads.

Setting `download_node_cache` to `true` will cache downloads directly on
the respective cluster node. This is only useful when `download_delegate`
is set as otherwise files and container images are directly downloaded
to their destination on each node.
Further, note that this is usually only useful for very specific use cases such as debugging or developing Kubespray.

With `download_cache` set to `true` all downloads are cached on
the host specified with `download_cache_host`.

Note that when using a `download_cache_host` other than `localhost` the machine will
have to be able to connect to the cluster nodes without password (due to a limitation of the Ansible rsync module).

The cache directory can be set for both cache types via `download_cache_dir` and `download_node_cache_dir`.

If a file or container image is available in the cache it is uploaded to the node which requires it.
In the case of node cache, the file or container image is directly used and no copying between
hosts is required.
Downloads are only triggered when the file or image is not present in the cache or the node's cache.

Note that caching files and container images on cluster nodes with `download_node_cache` enabled will require additional
storage space on each cluster node.

When using a download delegate and `download_delegate == download_cache_host` and `download_dir == download_cache_dir`
then the download directory is used as the cache directory meaning downloaded files are not removed after completion of
downloads.


## Download delegate

Downloads can be delegated to a cluster node or another host outside of the cluster.
The download delegate will download all files and images which are then uploaded to the cluster nodes.

For example, in order to set the download delegate to a cluster node
(in this case the first master node) set:
```yaml
download_delegate: "{{ groups['kube-master'][0] }}"
```

Note that in this case one cluster node will download all files and images for the cluster
including ones that are not required on that node. Sufficient storage must be available on that node.

To delegate downloading to another host outside of the cluster simply set
```yaml
download_delegate: "my-download-delegate.company.org"
```

Note that when using a `download_delegate` other than `localhost` the delegate host will
have to be able to connect to the cluster nodes without password (due to a limitation of the Ansible rsync module).

When using a download delegate `download_dir` determines the directory on the delegate where downloads are stored.

## Download sources

Download sources can be adjusted to custom requirements.

See also the [DNS stack docs](https://kubespray.io/#/docs/dns-stack) for the related intranet configuration,
so the hosts can resolve those urls and repos.

### Files

Files can be downloaded from user-defined sources.
Use the following variables:

* For files edit `<file>_version`, `<file>_download_url` and `<file>_checksum`.

The complete list of downloads is available in the download role's default variables
(`roles/download/defaults/main.yml`).

### Container images

To edit download sources of container images edit `<image>_image_repo` and `<image>_image_tag`
(and optionally `<image>_digest_checksum`).

Example to set custom download source for `dnsmasq`:
```
dnsmasq_digest_checksum: 7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193
dnsmasq_image_repo: andyshinn/dnsmasq
dnsmasq_image_tag: '2.72'
```

When using an insecure registry `<image>_image_repo`, you will certainly have to append them to the `docker_insecure_registries` variable.

Depending on the `container_manager` the following may also require adjustment:
  * When `container_manager=docker`, `docker_foo_repo_base_url`, `docker_foo_repo_gpgkey`, `dockerproject_bar_repo_base_url` and `dockerproject_bar_repo_gpgkey` (where `foo` is the distribution and `bar` is system package manager)
  * When `container_manager=crio`, `crio_rhel_repo_base_url`

The complete list of downloads is available in the download role's default variables
(`roles/download/defaults/main.yml`).

### Python

Consider adjusting `pyrepo_index` (and optionally `pyrepo_cert`).

### Helm

When using Helm adjust `helm_stable_repo_url`.

## Offline environment

There are various approaches to run Kubespray in an offline environment:

* Set download sources to file URLs and image registries that are available in your infrastructure.
* Use a download delegate and use a cache to store the downloaded artifacts on a host outside of the cluster
  (using `download_cache` and `download_cache_host`).
  The cached directory (`download_cache_dir`) could be used for several clusters providing offline installation.

In case your servers do not have direct access to the internet (for example when deploying on premises with security constraints)
remember to configure proxies correctly.


## Download strategy

For each cluster the individual cluster nodes are checked for whether the download is required.
If it is required and caching is enabled the required file or container image is uploaded to the respective
cluster nodes. Cluster node cache (`download_node_cache`) is checked before normal cache (`download_cache`).

If the download is not available in cache or caching is disabled, the file or image container is downloaded
by the `download_delegate` or the node itself if no download delegate is set. If `download_delegate` is set,
the downloaded file will be uploaded from the download delegate to the respective cluster nodes which require the download.

If caching is enabled and the download was not available in cache or has changed then the file or image
container will be loaded to the cache so that it is available next time (for example when scaling the
cluster with an additional node or provisioning a new cluster using the same cache host).

Note that building the cache on another host (with `download_cache` and `download_cache_host`) may require
increased time initially. However, once required downloads are available in cache, provisioning time will decrease.


## Variables

The following variables control the behaviour of the download role.

* `download_delegate` (default `''`): If set, downloads are delegated to the specified host.
* `download_cache` (default `false`): If set to `true` all downloads are cached.
    * `download_cache_host` (default `localhost`): If `download_cache` is true downloads are cached on the specified host.
    * `download_cache_dir` (default `/tmp/kubespray_cache`: If `download_cache` is true downloads are cached in the specified directory.
* `download_node_cache` (default `false`): If set to `true` nodes keep downloaded files and container images in a node local cache.
    * `download_node_cache_dir` (default `/tmp/kubespray_cache`): Determines the path where the node local cache is stored.
      Note that this directory is used to upload files to the nodes but removed afterwards if `download_node_cache` is `false`.

**Deprecated variables**:

* `download_run_once`: Can be achieved with `download_delegate`. At present the previous behaviour is preserved (the first master node is set as `download_delegate`.
* `download_localhost`: Same as setting `download_delegate: localhost`.
* `download_force_cache`: Use `download_cache`.
* `download_keep_remote_cache`: Use `download_node_cache`.
