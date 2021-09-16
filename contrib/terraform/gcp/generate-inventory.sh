#!/bin/bash

#
# Generates a inventory file based on the terraform output.
# After provisioning a cluster, simply run this command and supply the terraform state file
# Default state file is terraform.tfstate
#

set -e

usage () {
  echo "Usage: $0 <state file>" >&2
  exit 1
}

if [[ $# -ne 1 ]]; then
  usage
fi

TF_STATE_FILE=${1}

if [[ ! -f "${TF_STATE_FILE}" ]]; then
  echo "ERROR: state file ${TF_STATE_FILE} doesn't exist" >&2
  usage
fi

TF_OUT=$(terraform output -state "${TF_STATE_FILE}" -json)

MASTERS=$(jq -r '.master_ips.value | to_entries[]'  <(echo "${TF_OUT}"))
WORKERS=$(jq -r '.worker_ips.value | to_entries[]'  <(echo "${TF_OUT}"))
mapfile -t MASTER_NAMES < <(jq -r '.key'  <(echo "${MASTERS}"))
mapfile -t WORKER_NAMES < <(jq -r '.key'  <(echo "${WORKERS}"))

API_LB=$(jq -r '.control_plane_lb_ip_address.value' <(echo "${TF_OUT}"))

# Generate master hosts
i=1
for name in "${MASTER_NAMES[@]}"; do
  private_ip=$(jq -r '. | select( .key=='"\"${name}\""' ) | .value.private_ip'  <(echo "${MASTERS}"))
  public_ip=$(jq -r '. | select( .key=='"\"${name}\""' ) | .value.public_ip'  <(echo "${MASTERS}"))
  echo "${name} ansible_user=ubuntu ansible_host=${public_ip} ip=${private_ip} etcd_member_name=etcd${i}"
  i=$(( i + 1 ))
done

# Generate worker hosts
for name in "${WORKER_NAMES[@]}"; do
  private_ip=$(jq -r '. | select( .key=='"\"${name}\""' ) | .value.private_ip'  <(echo "${WORKERS}"))
  public_ip=$(jq -r '. | select( .key=='"\"${name}\""' ) | .value.public_ip'  <(echo "${WORKERS}"))
  echo "${name} ansible_user=ubuntu ansible_host=${public_ip} ip=${private_ip}"
done

echo ""
echo "[kube_control_plane]"
for name in "${MASTER_NAMES[@]}"; do
  echo "${name}"
done

echo ""
echo "[kube_control_plane:vars]"
echo "supplementary_addresses_in_ssl_keys = [ '${API_LB}' ]" # Add LB address to API server certificate
echo ""
echo "[etcd]"
for name in "${MASTER_NAMES[@]}"; do
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
