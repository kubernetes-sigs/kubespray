#!/bin/bash

set -e

create_mcp_conf() {
  echo "Create mcp config"
  cat > /root/mcp.conf << EOF
[builder]
push = True

[registry]
address = "127.0.0.1:31500"

[kubernetes]
environment = "openstack"

[repositories]
skip_empty = True
EOF
}

create_mirantis_mcp_conf() {
  echo "Create mcp config"
  cat > /root/mcp.conf << EOF
[builder]
push = False

[registry]
address = "registry01-bud.ng.mirantis.net:5800"
insecure = True

[kubernetes]
environment = "openstack"

[repositories]
skip_empty = True
EOF
}

create_resolvconf() {
  DNS_IP=`kubectl get service/kubedns --namespace=kube-system --template={{.spec.clusterIP}}`
  cat > /root/resolv.conf << EOF
search openstack.svc.cluster.local svc.cluster.local cluster.local default.svc.cluster.local svc.cluster.local cluster.local
nameserver $DNS_IP
options attempts:2
options ndots:5
EOF
}

create_registry() {
  if kubectl get pods | grep registry ; then
    echo "Registry is already running"
  else
    echo "Create registry"
    kubectl create -f registry_pod.yaml
    kubectl create -f registry_svc.yaml
  fi
}

build_images() {
  echo "Waiting for registry to start..."
  while true
  do
    STATUS=$(kubectl get pod | awk '/registry/ {print $3}')
    if [ "$STATUS" == "Running" ]
    then
      break
    fi
    sleep 1
  done
  mcp-microservices --config-file /root/mcp.conf build &> /var/log/mcp-build.log
}

hack_images() {
  # useless, but let's keep it just in case we need to hack something else
  for dir in ~/microservices-repos/ms-*/docker/* ; do
    cp /root/resolv.conf $dir/
    sed '/MAINTAINER/a COPY resolv.conf /var/tmp/resolv.conf' -i $dir/Dockerfile.j2
  done
}

# Switch to using prebuild images from ccp team
#create_mcp_conf
create_mirantis_mcp_conf
create_registry
#create_resolvconf
#build_images
