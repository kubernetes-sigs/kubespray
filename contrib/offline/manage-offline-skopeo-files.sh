#!/bin/bash
set -euo pipefail

OPTION=${1:-}
DOWNLOAD_NGINX=${DOWNLOAD_NGINX:-true}

CURRENT_DIR=$( dirname "$(readlink -f "$0")" )
OFFLINE_FILES_DIR_NAME="offline-files"
OFFLINE_FILES_DIR="${CURRENT_DIR}/${OFFLINE_FILES_DIR_NAME}"
OFFLINE_FILES_ARCHIVE="${CURRENT_DIR}/offline-files.tar.gz"
NGINX_IMAGE_ARCHIVE="${OFFLINE_FILES_DIR}/nginx-alpine.tar"
FILES_LIST=${FILES_LIST:-"${CURRENT_DIR}/temp/files.list"}
NGINX_PORT=${NGINX_PORT:-8080}

function detect_runtime() {
    for runtime in nerdctl podman docker; do
        if command -v "${runtime}" &>/dev/null 2>&1; then
            echo "${runtime}"
            return 0
        fi
    done
    return 1
}

function create_offline_files() {
    if [ ! -f "${FILES_LIST}" ]; then
        echo "[ERROR] ${FILES_LIST} not found, run ./generate_list.sh first"
        exit 1
    fi

    rm -rf "${OFFLINE_FILES_DIR}"
    rm -f "${OFFLINE_FILES_ARCHIVE}"
    mkdir -p "${OFFLINE_FILES_DIR}"

    case "$(uname -m)" in
        x86_64) TARGET_ARCH="amd64" ;;
        aarch64|arm64) TARGET_ARCH="arm64" ;;
        *) TARGET_ARCH="amd64" ;;
    esac
    TARGET_OS="linux"

    echo "[INFO] Downloading nginx:alpine image"
    if [ "${DOWNLOAD_NGINX}" = "true" ]; then
        if command -v skopeo &>/dev/null 2>&1; then
            skopeo copy \
                --override-os="${TARGET_OS}" --override-arch="${TARGET_ARCH}" \
                "docker://nginx:alpine" "docker-archive:${NGINX_IMAGE_ARCHIVE}:nginx:alpine"
        else
            runtime=$(detect_runtime) || { echo "[ERROR] No container runtime found"; exit 1; }
            echo "[INFO] Using ${runtime} to pull nginx:alpine"
            sudo "${runtime}" pull nginx:alpine
            sudo "${runtime}" save -o "${NGINX_IMAGE_ARCHIVE}" nginx:alpine
        fi
    else
        echo "[INFO] Skipping nginx download"
    fi

    echo "[INFO] Downloading files from list"
    while read -r url; do
        wget -nH --cut-dirs=2 -P "${OFFLINE_FILES_DIR}" "${url}" || echo "[WARN] Failed to download: ${url}"
    done < "${FILES_LIST}"

    tar -C "${CURRENT_DIR}" -czvf "${OFFLINE_FILES_ARCHIVE}" "${OFFLINE_FILES_DIR_NAME}"
    echo "[INFO] Done: ${OFFLINE_FILES_ARCHIVE}"
}

function serve_offline_files() {
    runtime=$(detect_runtime) || { echo "[ERROR] No container runtime found"; exit 1; }

    if [ -f "${OFFLINE_FILES_ARCHIVE}" ] && [ ! -d "${OFFLINE_FILES_DIR}" ]; then
        echo "[INFO] Extracting archive"
        tar -xzf "${OFFLINE_FILES_ARCHIVE}" -C "${CURRENT_DIR}"
    fi

    if [ ! -d "${OFFLINE_FILES_DIR}" ]; then
        echo "[ERROR] ${OFFLINE_FILES_DIR} not found"
        exit 1
    fi

    if sudo "${runtime}" container inspect nginx-files >/dev/null 2>&1; then
        echo "[INFO] nginx-files container already running"
        return 0
    fi

    if [ -f "${NGINX_IMAGE_ARCHIVE}" ]; then
        echo "[INFO] Loading nginx from local archive"
        sudo "${runtime}" load -i "${NGINX_IMAGE_ARCHIVE}"
    else
        echo "[WARN] nginx:alpine not found locally, attempting to pull"
    fi

    sudo --preserve-env=http_proxy,https_proxy,no_proxy "${runtime}" run \
        --restart=always -d -p "${NGINX_PORT}:80" \
        --volume "${OFFLINE_FILES_DIR}":/usr/share/nginx/html/download \
        --volume "${CURRENT_DIR}"/nginx.conf:/etc/nginx/nginx.conf \
        --name nginx-files nginx:alpine

    echo "[INFO] nginx serving at http://localhost:${NGINX_PORT}"
}

case "${OPTION}" in
    create)
        create_offline_files
        ;;
    serve)
        serve_offline_files
        ;;
    *)
        echo "Usage: $0 [create|serve]"
        echo "  create - download files and nginx image"
        echo "  serve  - start nginx server"
        echo ""
        echo "Environment variables:"
        echo "  DOWNLOAD_NGINX=false  - skip nginx download"
        ;;
esac
