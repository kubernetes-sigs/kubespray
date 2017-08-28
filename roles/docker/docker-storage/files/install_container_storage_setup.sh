#!/bin/sh

set -e

version=${1:-master}
profile_name=${2:-kubespray}
dir=`mktemp -d`
export GIT_DIR=$dir/.git
export GIT_WORK_TREE=$dir

git init
git fetch --depth 1 https://github.com/projectatomic/container-storage-setup.git $version
git merge FETCH_HEAD
make -C $dir install
rm -rf /var/lib/container-storage-setup/$profile_name $dir

set +e

/usr/bin/container-storage-setup create $profile_name /etc/sysconfig/docker-storage-setup && /usr/bin/container-storage-setup activate $profile_name
# FIXME: exit status can be 1 for both fatal and non fatal errors in current release, 
# could be improved by matching error strings 
exit 0
