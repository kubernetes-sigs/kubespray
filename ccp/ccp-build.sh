#!/bin/bash

set -e

create_mcp_conf() {
  echo "Create mcp config"
  cat > /root/mcp.conf << EOF
[builder]
push = True
registry = "127.0.0.1:31500"

[kubernetes]
environment = "openstack"

[repositories]
skip_empty = True
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

create_mcp_conf
create_registry
build_images
