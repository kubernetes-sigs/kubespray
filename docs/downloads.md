# Downloading binaries and containers

Kubespray supports several download/upload modes. The default is:

* Each node downloads binaries and container images on its own, which is ``download_run_once: False``.
* For K8s apps, pull policy is ``k8s_image_pull_policy: IfNotPresent``.
* For system managed containers, like kubelet or etcd, pull policy is ``download_always_pull: False``, which is pull if only the wanted repo and tag/sha256 digest differs from that the host has.

There is also a "pull once, push many" mode as well:

* Setting ``download_run_once: True`` will make kubespray download container images and binaries only once and then push them to the cluster nodes. The default download delegate node is the first `kube-master`.
* Set ``download_localhost: True`` to make localhost the download delegate. This can be useful if cluster nodes cannot access external addresses. To use this requires that docker is installed and running on the ansible master and that the current user is either in the docker group or can do passwordless sudo, to be able to access docker.

NOTE: When `download_run_once` is true and `download_localhost` is false, all downloads will be done on the delegate node, including downloads for container images that are not required on that node. As a consequence, the storage required on that node will probably be more than if download_run_once was false, because all images will be loaded into the docker instance on that node, instead of just the images required for that node.

On caching:

* When `download_run_once` is `True`, all downloaded files will be cached locally in `download_cache_dir`, which defaults to `/tmp/kubespray_cache`. On subsequent provisioning runs, this local cache will be used to provision the nodes, minimizing bandwidth usage and improving provisioning time. Expect about 800MB of disk space to be used on the ansible node for the cache. Disk space required for the image cache on the kubernetes nodes is a much as is needed for the largest image, which is currently slightly less than 150MB.
* By default, if `download_run_once` is false, kubespray will not retrieve the downloaded images and files from the remote node to the local cache, or use that cache to pre-provision those nodes. To force the use of the cache, set `download_force_cache` to `True`.
* By default, cached images that are used to pre-provision the remote nodes will be deleted from the remote nodes after use, to save disk space. Setting download_keep_remote_cache will prevent the files from being deleted. This can be useful while developing kubespray, as it can decrease provisioning times. As a consequence, the required storage for images on the remote nodes will increase from 150MB to about 550MB, which is currently the combined size of all required container images.

Container images and binary files are described by the vars like ``foo_version``,
``foo_download_url``, ``foo_checksum`` for binaries and ``foo_image_repo``,
``foo_image_tag`` or optional  ``foo_digest_checksum`` for containers.

Container images may be defined by its repo and tag, for example:
`andyshinn/dnsmasq:2.72`. Or by repo and tag and sha256 digest:
`andyshinn/dnsmasq@sha256:7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193`.

Note, the SHA256 digest and the image tag must be both specified and correspond
to each other. The given example above is represented by the following vars:

```yaml
dnsmasq_digest_checksum: 7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193
dnsmasq_image_repo: andyshinn/dnsmasq
dnsmasq_image_tag: '2.72'
```

The full list of available vars may be found in the download's ansible role defaults. Those also allow to specify custom urls and local repositories for binaries and container
images as well. See also the DNS stack docs for the related intranet configuration,
so the hosts can resolve those urls and repos.

## Offline environment

In case your servers don't have access to internet (for example when deploying on premises with security constraints), you'll have, first, to setup the appropriate proxies/caches/mirrors and/or internal repositories and registries and, then, adapt the following variables to fit your environment before deploying:

* At least `foo_image_repo` and `foo_download_url` as described before (i.e. in case of use of proxies to registries and binaries repositories, checksums and versions do not necessarily need to be changed).
  NOTE: Regarding `foo_image_repo`, when using insecure registries/proxies, you will certainly have to append them to the `docker_insecure_registries` variable in group_vars/all/docker.yml
* `pyrepo_index` (and optionally `pyrepo_cert`)
* Depending on the `container_manager`
  * When `container_manager=docker`, `docker_foo_repo_base_url`, `docker_foo_repo_gpgkey`, `dockerproject_bar_repo_base_url` and `dockerproject_bar_repo_gpgkey` (where `foo` is the distribution and `bar` is system package manager)
  * When `container_manager=crio`, `crio_rhel_repo_base_url`
* When using Helm, `helm_stable_repo_url`
