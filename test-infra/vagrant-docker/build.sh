#!/bin/sh
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 tag" >&2
  exit 1
fi

VERSION="$1"
IMG="quay.io/kubespray/vagrant:${VERSION}"

docker build . --build-arg "KUBESPRAY_VERSION=${VERSION}" --tag "$IMG"
docker push "$IMG"
