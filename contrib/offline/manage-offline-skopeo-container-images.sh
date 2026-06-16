#!/usr/bin/env bash
set -euo pipefail

OPTION=${1:-}
CURRENT_DIR=$(cd "$(dirname "$0")" && pwd)
TEMP_DIR=$(mktemp -d)
IMAGE_TAR_FILE="${CURRENT_DIR}/container-images.tar.gz"
IMAGE_DIR="${CURRENT_DIR}/container-images"
IMAGE_LIST="${IMAGE_DIR}/container-images.txt"
RETRY_COUNT=5

case "$(uname -m)" in
  x86_64)  TARGET_ARCH="amd64" ;;
  aarch64|arm64) TARGET_ARCH="arm64" ;;
  *) TARGET_ARCH="amd64" ;;
esac
TARGET_OS="linux"

function create_container_image_tar() {
  echo "[INFO] Platform: $(uname -s)/$(uname -m) -> ${TARGET_OS}/${TARGET_ARCH}"
  : "${IMAGES_FROM_FILE:?IMAGES_FROM_FILE must point to an images list file (e.g. contrib/offline/temp/images.list)}"
  echo "[INFO] Getting images from ${IMAGES_FROM_FILE}"
  [ -f "${IMAGES_FROM_FILE}" ] || { echo "[ERROR] ${IMAGES_FROM_FILE} not found"; exit 1; }
  IMAGES=$(realpath "${IMAGES_FROM_FILE}")


  rm -rf "${IMAGE_DIR}" "${IMAGE_TAR_FILE}"
  mkdir -p "${IMAGE_DIR}"
  cd "${IMAGE_DIR}"

  echo "[INFO] Downloading registry:latest"
  skopeo copy --override-os="${TARGET_OS}" --override-arch="${TARGET_ARCH}" \
    --src-tls-verify=false --retry-times="${RETRY_COUNT}" \
    "docker://registry:latest" "docker-archive:${IMAGE_DIR}/registry-latest.tar"

  total=$(wc -l < "${IMAGES}")
  n=0
  while read -r image || [ -n "${image}" ]; do
    n=$((n + 1))
    FILE_NAME="$(echo "${image}" | tr '/:' '--' | sed 's/@.*//').oci"

    echo "[${n}/${total}] ${image}"

    skopeo copy --override-os="${TARGET_OS}" --override-arch="${TARGET_ARCH}" \
      --src-tls-verify=false --retry-times="${RETRY_COUNT}" \
      "docker://${image}" "oci-archive:${IMAGE_DIR}/${FILE_NAME}" || \
    skopeo copy --all --src-tls-verify=false --retry-times="${RETRY_COUNT}" \
      "docker://${image}" "oci-archive:${IMAGE_DIR}/${FILE_NAME}"


    FIRST_PART=$(echo "${image}" | awk -F"/" '{print $1}')
    FIRST_PART_HOST=$(echo "${FIRST_PART}" | awk -F":" '{print $1}')
    if [[ "${FIRST_PART_HOST}" =~ ^(registry.k8s.io|gcr.io|ghcr.io|docker.io|quay.io)$ ]] || \
       [[ -n "${PRIVATE_REGISTRY:-}" && "${FIRST_PART_HOST}" = "${PRIVATE_REGISTRY}" ]]; then
      image=$(echo "${image}" | sed "s@^${FIRST_PART}/@@")
    fi
    echo "${FILE_NAME}  ${image}" >> "${IMAGE_LIST}"
  done < "${IMAGES}"

  cd ..
  tar -zcf "${IMAGE_TAR_FILE}" ./container-images

  echo "[INFO] Done: ${IMAGE_TAR_FILE}"
}

function register_container_images() {
  REGISTRY_PORT=${REGISTRY_PORT:-"5000"}

  if [ -z "${DESTINATION_REGISTRY:-}" ]; then
    DESTINATION_REGISTRY="localhost:${REGISTRY_PORT}"
    echo "[INFO] Creating local registry on ${DESTINATION_REGISTRY}"
    create_registry=true
  else
    echo "[INFO] Pushing to ${DESTINATION_REGISTRY}"
    create_registry=false
  fi

  [ -f "${IMAGE_TAR_FILE}" ] || { echo "[ERROR] ${IMAGE_TAR_FILE} not found"; exit 1; }
  mkdir -p "${TEMP_DIR}"

  if [ -d /etc/docker/ ] && [ -f "${CURRENT_DIR}/docker-daemon.json" ]; then
    sudo cp "${CURRENT_DIR}/docker-daemon.json" /etc/docker/daemon.json 2>/dev/null || echo "[WARN] Could not update docker daemon.json"
  elif [ -d /etc/containers/ ] && [ -f "${CURRENT_DIR}/registries.conf" ]; then
    sudo cp "${CURRENT_DIR}/registries.conf" /etc/containers/registries.conf 2>/dev/null || echo "[WARN] Could not update containers registries.conf"
  elif [ "$(uname -s)" != "Darwin" ]; then
    echo "[ERROR] No runtime config found"
    exit 1
  fi

  tar -zxf "${IMAGE_TAR_FILE}" -C "${CURRENT_DIR}"

  if ${create_registry}; then
    sudo "${runtime}" load -i "${IMAGE_DIR}/registry-latest.tar"
    sudo "${runtime}" container inspect registry >/dev/null 2>&1 || \
      sudo "${runtime}" run --restart=always -d -p "${REGISTRY_PORT}:${REGISTRY_PORT}" --name registry registry:latest
  fi

  total=$(wc -l < "${IMAGE_LIST}")
  n=0
  while read -r line; do
    n=$((n + 1))
    file_name=$(echo "${line}" | awk '{print $1}')
    raw_image=$(echo "${line}" | awk '{print $2}')
    new_image="${DESTINATION_REGISTRY}/${raw_image}"

    echo "[${n}/${total}] ${new_image}"
    skopeo copy --all --dest-tls-verify=false "oci-archive:${IMAGE_DIR}/${file_name}" "docker://${new_image}"
  done <<< "$(cat "${IMAGE_LIST}")"

  echo "[INFO] Done: registry ${DESTINATION_REGISTRY}"
}

runtime=""
for cmd in nerdctl podman docker; do
  if command -v "${cmd}" &>/dev/null; then
    runtime="${cmd}"
    break
  fi
done
[ -z "${runtime}" ] && { echo "[ERROR] No container runtime found"; exit 1; }


if ! command -v skopeo &>/dev/null 2>&1; then
    echo "[ERROR] skopeo not found"
    exit 1
fi

trap 'rm -rf "${TEMP_DIR}"' EXIT

case "${OPTION}" in
  create)   create_container_image_tar ;;
  register) register_container_images ;;
  *)
    echo "Usage: $0 [create|register]"
    echo "  IMAGES_FROM_FILE=<path>    - images list file"
    echo "  DESTINATION_REGISTRY=<h:p> - target registry"
    echo "  REGISTRY_PORT=<port>       - local port (default: 5000)"
    ;;
esac
