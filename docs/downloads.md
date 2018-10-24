Downloading binaries and containers
===================================

Kubespray supports several download/upload modes. The default is:

* Each node downloads binaries and container images on its own, which is
  ``download_run_once: False``.
* For K8s apps, pull policy is ``k8s_image_pull_policy: IfNotPresent``.
* For system managed containers, like kubelet or etcd, pull policy is
  ``download_always_pull: False``, which is pull if only the wanted repo and
  tag/sha256 digest differs from that the host has.

There is also a "pull once, push many" mode as well:

* Override the ``download_run_once: True`` to download container images only once
  then push to cluster nodes in batches. The default delegate node
  for pushing images is the first `kube-master`.
* If your ansible runner node (aka the admin node) have password-less sudo and
  docker enabled, you may want to define the ``download_localhost: True``, which
  makes that node a delegate for pushing images while running the deployment with
  ansible. This maybe the case if cluster nodes cannot access each over via ssh
  or you want to use local docker images as a cache for multiple clusters.

Container images and binary files are described by the vars like ``foo_version``,
``foo_download_url``, ``foo_checksum`` for binaries and ``foo_image_repo``,
``foo_image_tag`` or optional  ``foo_digest_checksum`` for containers.

Container images may be defined by its repo and tag, for example:
`andyshinn/dnsmasq:2.72`. Or by repo and tag and sha256 digest:
`andyshinn/dnsmasq@sha256:7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193`.

Note, the sha256 digest and the image tag must be both specified and correspond
to each other. The given example above is represented by the following vars:
```
dnsmasq_digest_checksum: 7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193
dnsmasq_image_repo: andyshinn/dnsmasq
dnsmasq_image_tag: '2.72'
```
The full list of available vars may be found in the download's ansible role defaults.
Those also allow to specify custom urls and local repositories for binaries and container
images as well. See also the DNS stack docs for the related intranet configuration,
so the hosts can resolve those urls and repos.

## Offline environment

In case your servers don't have access to internet (for example when deploying on premises with security constraints), you'll have, first, to setup the appropriate proxies/caches/mirrors and/or internal repositories and registries and, then, adapt the following variables to fit your environment before deploying:

* At least `foo_image_repo` and `foo_download_url` as described before (i.e. in case of use of proxies to registries and binaries repositories, checksums and versions do not necessarily need to be changed).
  NB: Regarding `foo_image_repo`, when using insecure registries/proxies, you will certainly have to append them to the `docker_insecure_registries` variable in group_vars/all/docker.yml
* `pyrepo_index` (and optionally `pyrepo_cert`)
* Depending on the `container_manager`
  * When `container_manager=docker`, `docker_foo_repo_base_url`, `docker_foo_repo_gpgkey`, `dockerproject_bar_repo_base_url` and `dockerproject_bar_repo_gpgkey` (where `foo` is the distribution and `bar` is system package manager)
  * When `container_manager=crio`, `crio_rhel_repo_base_url` 
* When using Helm, `helm_stable_repo_url`
