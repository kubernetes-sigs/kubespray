#!/bin/bash

# This file is part of Kargo.
#
#    Foobar is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Foobar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

#color variables
txtbld=$(tput bold)             # Bold
bldred=${txtbld}$(tput setaf 1) #  red
bldgre=${txtbld}$(tput setaf 2) #  green
bldylw=${txtbld}$(tput setaf 3) #  yellow
txtrst=$(tput sgr0)             # Reset
err=${bldred}ERROR${txtrst}
info=${bldgre}INFO${txtrst}
warn=${bldylw}WARNING${txtrst}

usage()
{
    cat << EOF
Update ansible playbook with a specific kubernetes version

Usage : $(basename $0) -v <k8s version>
      -h | --help         : Show this message
      -i | --init         : Initial upgrade (download binaries)
      -v | --version      : Kubernetes version
               
               ex : switch to kubernetes v1.2.4
               $(basename $0) -v v1.2.4
EOF
}

# Options parsing
while (($#)); do
    case "$1" in
        -h | --help)   usage;   exit 0;;
        -i | --init) INIT=1; shift;;
        -v | --version) VERS=${2}; shift 2;;
        *)
            usage
            echo "ERROR : Unknown option"
            exit 3
        ;;
    esac
done

if [ -z ${VERS} ]; then
    usage
    echo -e "\n${err}: The option version must be defined"
    exit 3
else
   if ! [[ ${VERS} =~ ^v[0-9]\.[0-9]\.[0-9]$ ]]; then
       echo -e "\n${err}: Invalid version format (ex: v1.2.4)"
       exit 1
   fi
fi

UPLOAD_VARFILE="roles/uploads/defaults/main.yml"
DOWNLOAD_VARFILE="roles/download/defaults/main.yml"
K8S_BIN="kubelet kubectl kube-apiserver"

if [[ ${INIT} -eq 1 ]]; then
   DOWNLOAD_URL=https://storage.googleapis.com/kubernetes-release/release/${VERS}/bin/linux/amd64
   TMP_DIR=$(mktemp -d --tmpdir kubernetes_tmpbin_XXXXXXX)
   sed -i "s/^hyperkube_image_tag.*$/hyperkube_image_tag: \"${VERS}\"/" roles/kubernetes/node/defaults/main.yml
   trap 'rm -rf "${tmpdir}"' EXIT
   cd "${tmpdir}"

   for BIN in ${K8S_BIN}; do
       curl -s -o ${BIN} ${DOWNLOAD_URL}/${BIN}
       if [ $? -ne 0 ]; then
           echo -e "\n${err}: Downloading ${BIN} failed! Try again"
           exit 1
       else
           echo -e "\n${info}: ${BIN} downloaded successfuly"
       fi
   done

   for varfile in ${UPLOAD_VARFILE} ${DOWNLOAD_VARFILE}; do
       sed -i "s/^kube_version.*$/kube_version: \"${VERS}\"/" ${varfile}
   
       for BIN in ${K8S_BIN}; do
           CHECKSUM=$(sha256sum ${BIN} | cut -d' ' -f1)
           BIN=$(echo ${BIN} | tr '-' '_')
           sed  -i "s/^${BIN}_checksum.*$/${BIN}_checksum: \"${CHECKSUM}\"/" ${varfile}
       done
   done
   
   rm -rf "${tmpdir}"
else
   CHECKSUM_URL=https://storage.googleapis.com/kargo/${VERS}_k8s-sha256
   sed -i "s/^hyperkube_image_tag.*$/hyperkube_image_tag: \"${VERS}\"/" roles/kubernetes/node/defaults/main.yml
    for varfile in ${UPLOAD_VARFILE} ${DOWNLOAD_VARFILE}; do
        sed -i "s/^kube_version.*$/kube_version: \"${VERS}\"/" ${varfile}
        for BIN in ${K8S_BIN}; do
            if [[ "${BIN}" =~ "apiserver" ]]; then
                BIN="apiserver"
            fi
            line=$(curl -sk ${CHECKSUM_URL} | grep ${BIN})
            CHECKSUM=$(echo ${line} | cut -d':' -f2)
            if [[ "${BIN}" =~ "apiserver" ]]; then
                BIN="kube_apiserver"
            fi
            sed  -i "s/^${BIN}_checksum.*$/${BIN}_checksum: \"${CHECKSUM}\"/" ${varfile}
        done
    done
fi
