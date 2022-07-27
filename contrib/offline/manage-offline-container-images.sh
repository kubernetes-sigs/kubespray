#!/bin/bash

OPTION=$1
CURRENT_DIR=$( dirname "$(readlink -f "$0")" )
TEMP_DIR="${CURRENT_DIR}/temp"
IMAGE_TAR_FILE="${CURRENT_DIR}/container-images.tar.gz"
IMAGE_DIR="${CURRENT_DIR}/container-images"
IMAGE_LIST="${IMAGE_DIR}/container-images.txt"
RETRY_COUNT=5

K8S_IMAGES_LIST_FILE=${K8S_IMAGES_LIST_FILE:-"${TEMP_DIR}/images.list"}
K8S_IMAGE_DIR="${CURRENT_DIR}/k8s-images"
K8S_IMAGE_INFO_FILE="${K8S_IMAGE_DIR}/images.info"
K8S_IMAGE_ARCHIVE="${CURRENT_DIR}/k8s-images.tar.gz"

function save_image_to_file() {
  image=$1
  info_file=$2
  if [ -z "${image}" ]; then
    echo "image should be provided."
    exit 1
  fi
  if [ -z "${info_file}" ]; then
    echo "info file should be provided."
    exit 1
  fi

  FILE_NAME="$(echo ${image} | sed s@"/"@"-"@g | sed s/":"/"-"/g)".tar
  [ -f "${FILE_NAME}" ] && return 0
  set +e
  for step in $(seq 1 ${RETRY_COUNT})
  do
    sudo docker pull ${image}
    if [ $? -eq 0 ]; then
      break
    fi
    echo "Failed to pull ${image} at step ${step}"
    if [ ${step} -eq ${RETRY_COUNT} ]; then
      exit 1
    fi
  done
  set -e
  sudo docker save -o "${FILE_NAME}"  "${image}"

  # NOTE: Here removes the following repo parts from each image
  # so that these parts will be replaced with Kubespray.
  # - kube_image_repo: "registry.k8s.io"
  # - gcr_image_repo: "gcr.io"
  # - docker_image_repo: "docker.io"
  # - quay_image_repo: "quay.io"
  FIRST_PART=$(echo "${image}" | awk -F"/" '{print $1}')
  if [ "${FIRST_PART}" = "registry.k8s.io" ] ||
     [ "${FIRST_PART}" = "gcr.io" ] ||
     [ "${FIRST_PART}" = "docker.io" ] ||
     [ "${FIRST_PART}" = "quay.io" ] ||
     [ "${FIRST_PART}" = "${PRIVATE_REGISTRY}" ]; then
    image=$(echo "${image}" | sed s@"${FIRST_PART}/"@@)
  fi
  echo "${FILE_NAME}  ${image}" >> "${info_file}"
}

function archive_k8s_images() {

  if [ ! -f "${K8S_IMAGES_LIST_FILE}" ]; then
    echo "K8s image list file ${K8S_IMAGES_LIST_FILE} do NOT exist, run generate_list.sh first."
    exit 1
  fi

  rm -rf "${K8S_IMAGE_DIR}"
  mkdir  "${K8S_IMAGE_DIR}"
  cd "${K8S_IMAGE_DIR}"

  images=$(cat "${K8S_IMAGES_LIST_FILE}")
  for image in ${images}
  do
    save_image_to_file "${image}" "${K8S_IMAGE_INFO_FILE}" || exit $?
  done

  cd "${OLDPWD}"

  sudo chown -R "${USER}" "${K8S_IMAGE_DIR}"
  tar czvf "${K8S_IMAGE_ARCHIVE}"  ./k8s-images
  rm -rf "${K8S_IMAGE_DIR}"

  echo ""
  echo "${K8S_IMAGE_ARCHIVE} is created, k8s deploy images inside."
  echo "Please sync this file to your offline environment, run \"${0} restore-k8s \" to have original-tagged images."

}

function create_container_image_tar() {
  set -e

  IMAGES=$(kubectl describe pods --all-namespaces | grep " Image:" | awk '{print $2}' | sort | uniq)
  # NOTE: etcd and pause cannot be seen as pods.
  # The pause image is used for --pod-infra-container-image option of kubelet.
  EXT_IMAGES=$(kubectl cluster-info dump | egrep "quay.io/coreos/etcd:|registry.k8s.io/pause:" | sed s@\"@@g)
  IMAGES="${IMAGES} ${EXT_IMAGES}"

  rm -f  "${IMAGE_TAR_FILE}"
  rm -rf "${IMAGE_DIR}"
  mkdir  "${IMAGE_DIR}"
  cd     "${IMAGE_DIR}"

  sudo docker pull registry:latest
  sudo docker save -o registry-latest.tar registry:latest

  for image in ${IMAGES}
  do
    save_image_to_file "${image}" "${IMAGE_LIST}" || exit $?
  done

  cd ..
  sudo chown -R "${USER}" "${IMAGE_DIR}"
  tar -zcvf "${IMAGE_TAR_FILE}"  ./container-images
  rm -rf "${IMAGE_DIR}"

  echo ""
  echo "${IMAGE_TAR_FILE} is created to contain your container images."
  echo "Please keep this file and bring it to your offline environment."
}

function restore_image_file() {
  file_name=$1
  raw_image=$2
  if [ -z "${file_name}" ]; then
    echo -n "Failed to get file_name"
    exit 1
  fi
  if [ -z "${raw_image}" ]; then
    echo -n "Failed to get raw_image"
    exit 1
  fi
  if [ ! -f "${IMAGE_DIR}/${file_name}" ]; then
    echo -n "image archive file ${IMAGE_DIR}/${file_name} do NOT exit"
    exit 1
  fi

  org_image=$(sudo docker load -i "${IMAGE_DIR}/${file_name}" | head -n1 | awk '{print $3}')
  if [ -z "${org_image}" ]; then
    echo "Failed to get org_image for line ${line}"
    exit 1
  fi

  image_id=$(sudo docker image inspect "${org_image}" | grep "\"Id\":" | awk -F: '{print $3}'| sed s/'\",'//)
  if [ -z "${image_id}" ]; then
    echo "Failed to get image_id for file ${file_name}"
    exit 1
  fi

  sudo docker load -i "${IMAGE_DIR}/${file_name}"
}

function restore_k8s_image_archives() {
  if [ ! -f "${IMAGE_LIST}" ]; then
    echo "image info file ${IMAGE_LIST} should exist."
    exit 1
  fi

  while read -r line; do
    file_name=$(echo "${line}" | awk '{print $1}')
    raw_image=$(echo "${line}" | awk '{print $2}')
    restore_image_file "${file_name}" "${raw_image}"
  done <<< "$(cat "${K8S_IMAGE_INFO_FILE}")"

}

function register_container_images() {
  if [ ! -f "${IMAGE_TAR_FILE}" ]; then
    echo "${IMAGE_TAR_FILE} should exist."
    exit 1
  fi
  if [ ! -d "${TEMP_DIR}" ]; then
    mkdir "${TEMP_DIR}"
  fi

  # To avoid "http: server gave http response to https client" error.
  LOCALHOST_NAME=$(hostname)
  if [ -d /etc/docker/ ]; then
    set -e
    # Ubuntu18.04, RHEL7/CentOS7
    cp "${CURRENT_DIR}/docker-daemon.json"    "${TEMP_DIR}/docker-daemon.json"
    sed -i s@"HOSTNAME"@"${LOCALHOST_NAME}"@  "${TEMP_DIR}/docker-daemon.json"
    sudo cp "${TEMP_DIR}/docker-daemon.json"  "/etc/docker/daemon.json"
  elif [ -d /etc/containers/ ]; then
    set -e
    # RHEL8/CentOS8
    cp "${CURRENT_DIR}/registries.conf"         "${TEMP_DIR}/registries.conf"
    sed -i s@"HOSTNAME"@"${LOCALHOST_NAME}"@  "${TEMP_DIR}/registries.conf"
    sudo cp "${TEMP_DIR}/registries.conf"   "/etc/containers/registries.conf"
  else
    echo "docker package(docker-ce, etc.) should be installed"
    exit 1
  fi

  tar -zxvf "${IMAGE_TAR_FILE}"
  sudo docker load -i "${IMAGE_DIR}/registry-latest.tar"
  set +e
  sudo docker container inspect registry >/dev/null 2>&1
  if [ $? -ne 0 ]; then
    sudo docker run --restart=always -d -p 5000:5000 --name registry registry:latest
  fi
  set -e

  while read -r line; do
    file_name=$(echo "${line}" | awk '{print $1}')
    raw_image=$(echo "${line}" | awk '{print $2}')

    restore_image_file "${file_name}" "${raw_image}"
    ret=$?
    if [ $ret -ne 0 ];then
      echo " for line ${line}"
      exit $?
    fi

    new_image="${LOCALHOST_NAME}:5000/${raw_image}"
    sudo docker tag  "${image_id}" "${new_image}"
    sudo docker push "${new_image}"
  done <<< "$(cat "${IMAGE_LIST}")"

  echo "Succeeded to register container images to local registry."
  echo "Please specify ${LOCALHOST_NAME}:5000 for the following options in your inventry:"
  echo "- kube_image_repo"
  echo "- gcr_image_repo"
  echo "- docker_image_repo"
  echo "- quay_image_repo"
}

if [ "${OPTION}" == "create" ]; then
  create_container_image_tar
elif [ "${OPTION}" == "register" ]; then
  register_container_images
elif [ "${OPTION}" == "archive-k8s" ]; then
  archive_k8s_images
elif [ "${OPTION}" == "restore-k8s" ]; then
  restore_k8s_image_archives
else
  echo "This script has two features:"
  echo "(1) Get container images from an environment which is deployed online."
  echo "(2) Deploy local container registry and register the container images to the registry."
  echo ""
  echo "Step(1) should be done online site as a preparation, then we bring"
  echo "the gotten images to the target offline environment. if images are from"
  echo "a private registry, you need to set PRIVATE_REGISTRY environment variable."
  echo "Then we will run step(2) for registering the images to local registry."
  echo ""
  echo "${IMAGE_TAR_FILE} is created to contain your container images."
  echo "Please keep this file and bring it to your offline environment."
  echo ""
  echo "Step(1) can be operated with:"
  echo " $ ./manage-offline-images.sh   archive-k8s #for k8s deploy images only"
  echo " $ ./manage-offline-container-images.sh   create  #for running k8s cluster images"
  echo ""
  echo "Step(2) can be operated with:"
  echo " $ ./manage-offline-images.sh   restore-k8s #restore k8s deploy images, restore tags"
  echo " $ ./manage-offline-container-images.sh   register   #for running k8s cluster images and pushing images"
  echo ""
  echo "Please specify 'create' or 'register' for container images,"
  echo " specify 'archive-k8s' or 'restore-k8s' for k8s deploy images."
  echo ""
  exit 1
fi
