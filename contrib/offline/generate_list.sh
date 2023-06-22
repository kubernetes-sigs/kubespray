#!/bin/bash
set -eo pipefail

CURRENT_DIR=$(cd $(dirname $0); pwd)
TEMP_DIR="${CURRENT_DIR}/temp"
REPO_ROOT_DIR="${CURRENT_DIR%/contrib/offline}"

: ${DOWNLOAD_YML:="roles/download/defaults/main/main.yml"}

mkdir -p ${TEMP_DIR}

# generate all download files url template
grep 'download_url:' ${REPO_ROOT_DIR}/${DOWNLOAD_YML} \
    | sed 's/^.*_url: //g;s/\"//g' > ${TEMP_DIR}/files.list.template

# generate all images list template
sed -n '/^downloads:/,/download_defaults:/p' ${REPO_ROOT_DIR}/${DOWNLOAD_YML} \
    | sed -n "s/repo: //p;s/tag: //p" | tr -d ' ' \
    | sed 'N;s#\n# #g' | tr ' ' ':' | sed 's/\"//g' > ${TEMP_DIR}/images.list.template

# add kube-* images to images list template
# Those container images are downloaded by kubeadm, then roles/download/defaults/main/main.yml
# doesn't contain those images. That is reason why here needs to put those images into the
# list separately.
KUBE_IMAGES="kube-apiserver kube-controller-manager kube-scheduler kube-proxy"
for i in $KUBE_IMAGES; do
    echo "{{ kube_image_repo }}/$i:{{ kube_version }}" >> ${TEMP_DIR}/images.list.template
done

# run ansible to expand templates
/bin/cp ${CURRENT_DIR}/generate_list.yml ${REPO_ROOT_DIR}

(cd ${REPO_ROOT_DIR} && ansible-playbook $* generate_list.yml && /bin/rm generate_list.yml) || exit 1
