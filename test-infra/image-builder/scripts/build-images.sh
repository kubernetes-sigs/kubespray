#!/usr/bin/env bash
set -euo pipefail

IMAGES_YAML="test-infra/image-builder/roles/kubevirt-images/defaults/main.yml"
WORKDIR="${WORKDIR:-/tmp/kubevirt-images}"

mkdir -p "$WORKDIR"

yq -r '.images | keys[]' "$IMAGES_YAML" | while read -r image; do
  echo "==> Processing $image"

  filename=$(yq -r ".images.\"$image\".filename" "$IMAGES_YAML")
  url=$(yq -r ".images.\"$image\".url" "$IMAGES_YAML")
  checksum=$(yq -r ".images.\"$image\".checksum" "$IMAGES_YAML")
  converted=$(yq -r ".images.\"$image\".converted" "$IMAGES_YAML")
  tag=$(yq -r ".images.\"$image\".tag" "$IMAGES_YAML")

  image_path="$WORKDIR/$filename"

  curl -L "$url" -o "$image_path"

  if [[ "$checksum" == sha256:* ]]; then
    echo "${checksum#sha256:}  $image_path" | sha256sum -c -
  else
    echo "${checksum#sha512:}  $image_path" | sha512sum -c -
  fi

  if [[ "$converted" == "true" ]]; then
    qemu-img convert -O qcow2 "$image_path" "$image_path.converted"
    image_path="$image_path.converted"
  fi

  docker build \
    --build-arg IMAGE="$image_path" \
    -t quay.io/kubespray/$image:$tag \
    test-infra/image-builder/docker

  docker push quay.io/kubespray/$image:$tag
done

