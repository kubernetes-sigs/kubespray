# vagrant docker image

This image is used for the vagrant CI jobs. It is using the libvirt driver.

## Usage

```console
$ docker run --net host --rm -it -v /var/run/libvirt/libvirt-sock:/var/run/libvirt/libvirt-sock quay.io/kubespray/vagrant
$ vagrant up
Bringing machine 'k8s-1' up with 'libvirt' provider...
Bringing machine 'k8s-2' up with 'libvirt' provider...
Bringing machine 'k8s-3' up with 'libvirt' provider...
[...]
```

## Cache

You can set `/root/kubespray_cache` as a volume to keep cache between runs.

## Building

```shell
./build.sh v2.12.5
```

## CI build check

The `image-build` matrix builds both Dockerfiles without publishing images, independently of `pipeline-image`. Vagrant uses the published base configured in `.gitlab-ci/build.yml`, not the newly built image. No VMs are started.

Run locally from the repository root:

```shell
docker build --platform linux/amd64 .
docker build --platform linux/amd64 \
  --build-arg KUBESPRAY_VERSION=v2.32.0 test-infra/vagrant-docker
```
