#!/bin/bash

CURRENT_DIR=$(cd $(dirname $0); pwd)
OFFLINE_FILES_DIR="${CURRENT_DIR}/offline-files"
FILES_LIST=${FILES_LIST:-"${CURRENT_DIR}/temp/files.list"}
NGINX_PORT=8080

# download files
if [ ! -f ${FILES_LIST} ]; then
    echo "${FILES_LIST} should exist."
    exit 1
fi
rm -rf ${OFFLINE_FILES_DIR}
mkdir  ${OFFLINE_FILES_DIR}
wget -x -P ${OFFLINE_FILES_DIR} -i ${FILES_LIST}

# run nginx container server
if command -v nerdctl 1>/dev/null 2>&1; then
    runtime="nerdctl"
elif command -v podman 1>/dev/null 2>&1; then
    runtime="podman"
elif command -v docker 1>/dev/null 2>&1; then
    runtime="docker"
else
    echo "No supported container runtime found"
    exit 1
fi
sudo "${runtime}" container inspect nginx >/dev/null 2>&1
if [ $? -ne 0 ]; then
    sudo "${runtime}" run \
        --restart=always -d -p ${NGINX_PORT}:80 \
        --volume ${OFFLINE_FILES_DIR}:/usr/share/nginx/html/download \
        --volume "$(pwd)"/nginx.conf:/etc/nginx/nginx.conf \
        --name nginx nginx:alpine
fi
