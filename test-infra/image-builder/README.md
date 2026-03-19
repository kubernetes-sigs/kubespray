# KubeVirt Image Builder

Build and push KubeVirt VM disk images to quay.io for Kubespray CI testing.

## How It Works

The Ansible playbook downloads upstream cloud images, converts them to qcow2, resizes (+8G), wraps each in a Docker image based on `kubevirt/registry-disk-v1alpha`, and pushes to `quay.io/kubespray/vm-<os-name>:<tag>`.

## Prerequisites

- Docker, `qemu-img`, Ansible
- Push access to [quay.io/kubespray](https://quay.io/organization/kubespray) (robot account `kubespray+buildvmimages`)

## Image Definitions

All OS images are defined in [`roles/kubevirt-images/defaults/main.yml`](roles/kubevirt-images/defaults/main.yml).

Each entry specifies:

| Field | Description |
|-------|-------------|
| `filename` | Downloaded file name |
| `url` | Upstream cloud image URL |
| `checksum` | Checksum for download verification |
| `converted` | `true` if the source is already qcow2, `false` if conversion is needed |
| `tag` | Docker image tag (usually `latest`) |

## Usage

### Build and push all images

```bash
cd test-infra/image-builder/
make docker_password=<quay-robot-token>
```

### Add a new OS image

1. Add a new entry to `roles/kubevirt-images/defaults/main.yml`:

   ```yaml
   new-os-name:
     filename: cloud-image-file.qcow2
     url: https://example.com/cloud-image-file.qcow2
     checksum: sha256:<hash>
     converted: true
     tag: "latest"
   ```

2. Build and push the image:

   ```bash
   make docker_password=<quay-robot-token>
   ```

3. Submit a PR with the `defaults/main.yml` change so CI can use the new image.
   See [#12379](https://github.com/kubernetes-sigs/kubespray/pull/12379) for an example.
