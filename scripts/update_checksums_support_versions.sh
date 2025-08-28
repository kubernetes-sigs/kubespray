#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  update_checksums_supported_versions.sh
#
#  Description:
#    This script is designed for experimental environments only,
#    to add support for newly released Kubernetes & Etcd versions
#    in Kubespray defaults (download.yml/checksums.yml).
#
#    Note: This process is NOT validated or recommended by the
#    official Kubespray community. Use only at your own risk
#    for testing and experimentation.
#
#  Features:
#    - Backup existing defaults/vars YAML files
#    - Download and update kubeadm/kubelet/kubectl/etcd sha256
#    - Update supported versions mappings
#    - Reuse previous "minor version" entries for crictl/crio/
#      pod_infra/snapshot_controller when adding new k8s version
#    - Dry-run mode with YAML patch preview
#    - Optional auto-install of yq if not present
#
# ============================================================

usage() {
  cat <<EOF
Usage: $(basename "$0") --k8s-version <VERSION> --etcd-version <VERSION> [OPTIONS]

Examples:
  $(basename "$0") --k8s-version 1.33.0 --etcd-version 3.5.22
  $(basename "$0") --k8s-version 1.33.0 --etcd-version 3.5.22 --arch arm64 --platform linux
  $(basename "$0") --k8s-version 1.33.0 --etcd-version 3.5.22 --dry-run

Options:
  --k8s-version VERSION     Kubernetes Version, e.g. 1.33.4
  --etcd-version VERSION    Etcd Version, e.g. 3.5.22
  --arch ARCH               Target architecture (default: amd64)
  --platform PLATFORM       Target platform/OS (default: linux)
  --dry-run                 Print intended updates only, do not modify files
  -h, --help                Show usage
EOF
}

# ==============================
# Options Parse
# ==============================
K8S_VERSION=""
ETCD_VERSION=""
ARCH="amd64"
PLATFORM="linux"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --k8s-version)   K8S_VERSION=$2; shift 2;;
    --etcd-version)  ETCD_VERSION=$2; shift 2;;
    --arch)          ARCH=$2; shift 2;;
    --platform)      PLATFORM=$2; shift 2;;
    --dry-run)       DRY_RUN=true; shift;;
    -h|--help)       usage; exit 0;;
    *) echo "[ERROR] Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "$K8S_VERSION" || -z "$ETCD_VERSION" ]]; then
  echo "[ERROR] --k8s-version and --etcd-version must be provided" >&2
  usage; exit 1
fi

K8S_MAJOR_MINOR=$(echo ${K8S_VERSION} | cut -d. -f1,2)
PREV_MAJOR_MINOR=$(awk -F. -v ver=${K8S_MAJOR_MINOR} 'BEGIN{split(ver,a,"."); print a[1]"."(a[2]-1)}')

BASE_DIR="../roles/kubespray_defaults"
DEFAULTS_FILE="${BASE_DIR}/defaults/main/download.yml"
CHECKSUMS_FILE="${BASE_DIR}/vars/main/checksums.yml"

# ==============================
# Ensure yq Exists
# ==============================
if ! command -v yq >/dev/null 2>&1; then
  echo "[INFO] yq not found, installing..."
  curl -sSL "https://github.com/mikefarah/yq/releases/latest/download/yq_${PLATFORM}_${ARCH}" -o /usr/local/bin/yq
  chmod +x /usr/local/bin/yq
  echo "[INFO] yq installed at /usr/local/bin/yq"
fi

# ==============================
# Backup Files
# ==============================
timestamp=$(date +%Y%m%d%H%M%S)
if [[ "$DRY_RUN" == false ]]; then
  cp -a $DEFAULTS_FILE $DEFAULTS_FILE.bak.$timestamp
  cp -a $CHECKSUMS_FILE $CHECKSUMS_FILE.bak.$timestamp
  echo "[INFO] Backup created with suffix .$timestamp"
else
  echo "[DRY-RUN] Skip backup files"
fi

# ==============================
# Fetch SHA256 for binaries
# ==============================
KUBEADM_SHA_TEMP=$(curl -sSL https://dl.k8s.io/v${K8S_VERSION}/bin/${PLATFORM}/${ARCH}/kubeadm.sha256)
KUBELET_SHA_TEMP=$(curl -sSL https://dl.k8s.io/v${K8S_VERSION}/bin/${PLATFORM}/${ARCH}/kubelet.sha256)
KUBECTL_SHA_TEMP=$(curl -sSL https://dl.k8s.io/v${K8S_VERSION}/bin/${PLATFORM}/${ARCH}/kubectl.sha256)
ETCD_SHA_TEMP=$(curl -sSL https://github.com/etcd-io/etcd/releases/download/v${ETCD_VERSION}/SHA256SUMS \
                  | grep etcd-v${ETCD_VERSION}-${PLATFORM}-${ARCH}.tar.gz | awk '{print $1}')

KUBEADM_SHA="sha256:${KUBEADM_SHA_TEMP}"
KUBELET_SHA="sha256:${KUBELET_SHA_TEMP}"
KUBECTL_SHA="sha256:${KUBECTL_SHA_TEMP}"
ETCD_SHA="sha256:${ETCD_SHA_TEMP}"

# ==============================
# Query helper: avoid duplicates
# ==============================
yq_query() {
  local map_expr=$1 key=$2 file=$3
  yq e "$map_expr | has(\"$key\")" "$file" | grep -q true
}

# ==============================
# Dry-run cache
# ==============================
NEW_CHECKSUMS=""
NEW_VERSIONS=""

yq_set() {
  local map_expr=$1 file=$2 desc=$3 key=$4 value=$5
  if yq_query "$map_expr" "$key" "$file"; then
    echo "[INFO] $desc already exists: $key -> $value (skip)"
    return
  fi
  if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] Would set $desc: $key -> $value"
    if [[ "$file" =~ checksums.yml ]]; then
      NEW_CHECKSUMS="$NEW_CHECKSUMS
  $key: \"$value\""
    else
      NEW_VERSIONS="$NEW_VERSIONS
  $key: \"$value\""
    fi
  else
    yq e -i "$map_expr[\"$key\"] = \"$value\"" "$file"
  fi
}

# ==============================
# Update checksums.yml
# ==============================

yq_set ".kubeadm_checksums.${ARCH}" \
       $CHECKSUMS_FILE "kubeadm checksum" \
       $K8S_VERSION $KUBEADM_SHA
yq_set ".kubelet_checksums.${ARCH}" \
       $CHECKSUMS_FILE "kubelet checksum" \
       $K8S_VERSION $KUBELET_SHA
yq_set ".kubectl_checksums.${ARCH}" \
       $CHECKSUMS_FILE "kubectl checksum" \
       $K8S_VERSION $KUBECTL_SHA
yq_set ".etcd_binary_checksums.${ARCH}" \
       $CHECKSUMS_FILE "etcd checksum" \
       ${ETCD_VERSION#v} $ETCD_SHA

# ==============================
# Update supported versions
# ==============================
yq_set ".etcd_supported_versions" \
       $DEFAULTS_FILE "etcd_supported_versions" \
       $K8S_MAJOR_MINOR ${ETCD_VERSION#v}

for dict in crictl_supported_versions crio_supported_versions pod_infra_supported_versions snapshot_controller_supported_versions; do
    prev_val=$(yq e ".${dict}[\"${PREV_MAJOR_MINOR}\"]" "$DEFAULTS_FILE")
    if [[ "$prev_val" != "null" ]]; then
      yq_set ".${dict}" \
             "$DEFAULTS_FILE" \
             "$dict" \
             "$K8S_MAJOR_MINOR" \
             "$prev_val"
    else
      echo "[WARN] $dict has no entry for $PREV_MAJOR_MINOR, skipped"
    fi
done

# ==============================
# Final Output
# ==============================
if [[ "$DRY_RUN" == true ]]; then
  echo
  echo "======= DRY-RUN FINAL checksums.yml PATCH ======="
  echo "$NEW_CHECKSUMS" | sed '/^$/d'
  echo
  echo "======= DRY-RUN FINAL download.yml PATCH ======="
  echo "$NEW_VERSIONS" | sed '/^$/d'
  echo
  echo "[DRY-RUN DONE] No files were modified."
else
  echo "[DONE] Updated supported_versions for Kubernetes $K8S_VERSION with etcd $ETCD_VERSION"
fi
