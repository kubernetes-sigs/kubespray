# Offline deployment

## Steps

* generate offline archive files.
* sync the archive files(and current offline directory) to offline environment.
* unarchive archive files and restore.

### on internet-available machine

```shell
./generate_list.sh
./manage-offline-images.sh archive-k8s #docker required
env NO_HTTP_SERVER=true ./manage-offline-files.sh
tar czvf offline-scripts.tar.gz manage*sh
tar cvf offline-all.tar k8s-images.tar.gz offline-files.tar.gz offline-scripts.tar.gz
<sync_method> offline-all.tar <dest_offline_machine>
```

### on offline machine

```shell
tar xvf offline-all.tar
tar xzvf k8s-images.tar.gz
tar xzvf offline-files.tar.gz
tar xzvf offline-scripts.tar.gz
./manage-offline-images.sh restore-k8s #docker required
```

## generate_list.sh

This script generates the list of downloaded files and the list of container images by `roles/download/defaults/main.yml` file.

Run this script will execute `generate_list.yml` playbook in kubespray root directory and generate four files,
all downloaded files url in files.list, all container images in images.list, jinja2 templates in *.template.

```shell
./generate_list.sh
tree temp
temp
├── files.list
├── files.list.template
├── images.list
└── images.list.template
0 directories, 5 files
```

In some cases you may want to update some component version, you can declare version variables in ansible inventory file or group_vars,
then run `./generate_list.sh -i [inventory_file]` to update file.list and images.list.

## manage-offline-files.sh

This script will download all files according to `temp/files.list` and run nginx container to provide offline file download.

Step(1) generate `files.list`

```shell
./generate_list.sh
```

Step(2) download files and run nginx container

```shell
./manage-offline-files.sh
```

when nginx container is running, it can be accessed through <http://127.0.0.1:8080/>.

## manage-offline-container-images.sh

Container image collecting script for offline deployment

This script has two features:
(1) Get container images from an environment which is deployed online.
(2) Deploy local container registry and register the container images to the registry.

Step(1) should be done online site as a preparation, then we bring the gotten images
to the target offline environment. if images are from a private registry,
you need to set `PRIVATE_REGISTRY` environment variable.
Then we will run step(2) for registering the images to local registry.

Step(1) can be operated with:

```shell
./manage-offline-images.sh   archive-k8s #for k8s deploy images only"
./manage-offline-container-images.sh   create  #for running k8s cluster images"
```

Step(2) can be operated with:

```shell
./manage-offline-images.sh   restore-k8s #restore k8s deploy images, restore tags"
./manage-offline-container-images.sh   register   #for running k8s cluster images and pushing images"
```
