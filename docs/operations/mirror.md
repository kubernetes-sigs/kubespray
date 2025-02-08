# Public Download Mirror

The public mirror is useful to make the public resources download quickly in some areas of the world. (such as China).

## Configuring Kubespray to use a mirror site

You can follow the [offline](offline-environment.md) to config the image/file download configuration to the public mirror site. If you want to download quickly in China, the configuration can be like:

```shell
# this should be in <your_inventory>/group_vars/k8s_cluster.yml
gcr_image_repo: "gcr.m.daocloud.io"
kube_image_repo: "k8s.m.daocloud.io"
docker_image_repo: "docker.m.daocloud.io"
quay_image_repo: "quay.m.daocloud.io"
github_image_repo: "ghcr.m.daocloud.io"

files_repo: "https://files.m.daocloud.io"
```

Use mirror sites only if you trust the provider. The Kubespray team cannot verify their reliability or security.
You can replace the `m.daocloud.io` with any site you want.

## Community-run mirror sites

DaoCloud(China)

* [image-mirror](https://github.com/DaoCloud/public-image-mirror)
* [files-mirror](https://github.com/DaoCloud/public-binary-files-mirror)
