#!/bin/bash

#
# Generates a inventory file based on the terraform output.
# After provisioning a cluster, simply run this command and supply the terraform state file
# Default state file is terraform.tfstate
#

set -e

TF_OUT=$(terraform output -json)

CONTROL_PLANES=$(jq -r '.kubernetes_cluster.value.control_plane_info | to_entries[]'  <(echo "${TF_OUT}"))
WORKERS=$(jq -r '.kubernetes_cluster.value.worker_info | to_entries[]'  <(echo "${TF_OUT}"))
mapfile -t CONTROL_PLANE_NAMES < <(jq -r '.key'  <(echo "${CONTROL_PLANES}"))
mapfile -t WORKER_NAMES < <(jq -r '.key'  <(echo "${WORKERS}"))

API_LB=$(jq -r '.kubernetes_cluster.value.control_plane_lb' <(echo "${TF_OUT}"))

echo "[all]"
# Generate control plane hosts
i=1
for name in "${CONTROL_PLANE_NAMES[@]}"; do
  private_ip=$(jq -r '. | select( .key=='"\"${name}\""' ) | .value.private_ip'  <(echo "${CONTROL_PLANES}"))
  echo "${name} ansible_user=root ansible_host=${private_ip} access_ip=${private_ip} ip=${private_ip} etcd_member_name=etcd${i}"
  i=$(( i + 1 ))
done

# Generate worker hosts
for name in "${WORKER_NAMES[@]}"; do
  private_ip=$(jq -r '. | select( .key=='"\"${name}\""' ) | .value.private_ip'  <(echo "${WORKERS}"))
  echo "${name} ansible_user=root ansible_host=${private_ip} access_ip=${private_ip} ip=${private_ip}"
done

API_LB=$(jq -r '.kubernetes_cluster.value.control_plane_lb'  <(echo "${TF_OUT}"))

echo ""
echo "[all:vars]"
echo "upstream_dns_servers=['8.8.8.8','8.8.4.4']"
echo "loadbalancer_apiserver={'address':'${API_LB}','port':'6443'}"


echo ""
echo "[kube_control_plane]"
for name in "${CONTROL_PLANE_NAMES[@]}"; do
  echo "${name}"
done

echo ""
echo "[etcd]"
for name in "${CONTROL_PLANE_NAMES[@]}"; do
  echo "${name}"
done

echo ""
echo "[kube_node]"
for name in "${WORKER_NAMES[@]}"; do
  echo "${name}"
done

echo ""
echo "[k8s_cluster:children]"
echo "kube_control_plane"
echo "kube_node"
