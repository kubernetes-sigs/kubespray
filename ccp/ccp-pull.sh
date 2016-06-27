#!/bin/bash

set -e

GERRIT_USER=${1:-$USER}
LOCAL_REPO="microservices-repos"
PROTO="ssh://$GERRIT_USER@"
REMOTE_REPOS="
review.fuel-infra.org:29418/nextgen/ms-aodh
review.fuel-infra.org:29418/nextgen/ms-ceilometer
review.fuel-infra.org:29418/nextgen/ms-ceph
review.fuel-infra.org:29418/nextgen/ms-cinder
review.fuel-infra.org:29418/nextgen/ms-debian-base
review.fuel-infra.org:29418/nextgen/ms-designate
review.fuel-infra.org:29418/nextgen/ms-elasticsearch
review.fuel-infra.org:29418/nextgen/ms-ext-config
review.fuel-infra.org:29418/nextgen/ms-glance
review.fuel-infra.org:29418/nextgen/ms-grafana
review.fuel-infra.org:29418/nextgen/ms-heat
review.fuel-infra.org:29418/nextgen/ms-horizon
review.fuel-infra.org:29418/nextgen/ms-influxdb
review.fuel-infra.org:29418/nextgen/ms-ironic
review.fuel-infra.org:29418/nextgen/ms-keystone
review.fuel-infra.org:29418/nextgen/ms-kibana
review.fuel-infra.org:29418/nextgen/ms-lma
review.fuel-infra.org:29418/nextgen/ms-magnum
review.fuel-infra.org:29418/nextgen/ms-manila
review.fuel-infra.org:29418/nextgen/ms-mariadb
review.fuel-infra.org:29418/nextgen/ms-memcached
review.fuel-infra.org:29418/nextgen/ms-mistral
review.fuel-infra.org:29418/nextgen/ms-mongodb
review.fuel-infra.org:29418/nextgen/ms-murano
review.fuel-infra.org:29418/nextgen/ms-neutron
review.fuel-infra.org:29418/nextgen/ms-nova
review.fuel-infra.org:29418/nextgen/ms-openstack-base
review.fuel-infra.org:29418/nextgen/ms-openvswitch
review.fuel-infra.org:29418/nextgen/ms-rabbitmq
review.fuel-infra.org:29418/nextgen/ms-sahara
review.fuel-infra.org:29418/nextgen/ms-swift
review.fuel-infra.org:29418/nextgen/ms-tempest
review.fuel-infra.org:29418/nextgen/ms-toolbox
review.fuel-infra.org:29418/nextgen/ms-trove
review.fuel-infra.org:29418/nextgen/ms-zaqar
"

cleanup() {
  mkdir -p $LOCAL_REPO
  rm -rf $LOCAL_REPO/ms-*
  rm -rf microservices
}

fetch_mcp() {
  git clone "${PROTO}review.fuel-infra.org:29418/nextgen/microservices"
  pushd microservices
  git review -d 22325
  popd
}

fetch_repos() {
  pushd $LOCAL_REPO
  for remote in $REMOTE_REPOS ; do
    git clone "${PROTO}${remote}"
  done
  popd
}

fetch_app_def() {
  echo "Fetch app-def repos"
  mariadb=21637
  keystone=21848
  memcached=21849
  rabbitmq=22053
  horizon=21850
  neutron=21886
  ovs=21951
  nova=21871
  glance=21998

  cd $LOCAL_REPO

  cd ms-mariadb
  git review -d $mariadb
  cd -
  cd ms-keystone
  git review -d $keystone
  cd -
  cd ms-memcached
  git review -d $memcached
  cd -
  cd ms-rabbitmq
  git review -d $rabbitmq
  cd -
  cd ms-horizon
  git review -d $horizon
  cd -
  cd ms-neutron
  git review -d $neutron
  cd -
  cd ms-openvswitch
  git review -d $ovs
  cd -
  cd ms-nova
  git review -d $nova
  cd -
  cd ms-glance
  git review -d $glance
  cd -
}

cleanup
fetch_mcp
fetch_repos
fetch_app_def

echo "Microservices pull is complete"
