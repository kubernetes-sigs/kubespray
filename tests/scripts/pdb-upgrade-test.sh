#!/usr/bin/env bash
# tests/scripts/pdb-upgrade-test.sh
#
# Demonstrates the graceful_rolling sliding-window advantage over linear when a
# PodDisruptionBudget blocks one worker node during an upgrade.
#
# Topology (3 workers, concurrency=2):
#   graceful_rolling  →  k8s-5 upgrades while k8s-4 is blocked; k8s-6 starts as
#                         soon as k8s-5 finishes (sliding window).
#   linear (serial 2) →  batch[k8s-4, k8s-5] stalls until k8s-4's drain succeeds;
#                         k8s-6 cannot start at all until the batch is complete.
#
# Usage:
#   bash tests/scripts/pdb-upgrade-test.sh [graceful_rolling|linear]
#
# Environment overrides:
#   KUBE_VERSION      Target Kubernetes version.  Default: 1.35.1
#   CONCURRENCY       upgrade_node_concurrency.   Default: 2
#   PDB_HOLD_SECONDS  Seconds to hold the PDB after k8s-4 is cordoned.
#                     Must be less than drain_timeout (360 s default).
#                     Default: 300
#   CP_HOST           SSH target for kubectl.     Default: vagrant@192.168.56.101
#   SSH_KEY           SSH identity file.          Default: ~/.vagrant.d/insecure_private_key
#
# Prerequisites:
#   - 6-node Vagrant cluster at v1.34.4 is running.
#   - kubespray .venv is in /home/jelinek/git/kubespray/.venv
#   - Run once per strategy; destroy/recreate the cluster between the two runs.
#
# Expected outcome:
#   graceful_rolling  →  k8s-5 and k8s-6 uncordon *before* the PDB is lifted.
#   linear            →  k8s-5 and k8s-6 can only uncordon *after* the PDB is lifted.
#   Total worker-phase time savings with graceful_rolling: ≈ 1× node_upgrade_time.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
STRATEGY="${1:-graceful_rolling}"
KUBE_VERSION="${KUBE_VERSION:-1.35.1}"
CONCURRENCY="${CONCURRENCY:-2}"
PDB_HOLD_SECONDS="${PDB_HOLD_SECONDS:-300}"    # must be < drain_timeout (360 s)
CP_HOST="${CP_HOST:-vagrant@192.168.56.101}"
SSH_KEY="${SSH_KEY:-$HOME/.vagrant.d/insecure_private_key}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST="$REPO_ROOT/tests/files/pdb-test/nginx-pdb.yml"
INVENTORY="$REPO_ROOT/.vagrant/provisioners/ansible/inventory"
UPGRADE_LOG="/tmp/pdb-upgrade-${STRATEGY}.log"
MONITOR_LOG="/tmp/pdb-monitor-${STRATEGY}.log"

SSHOPTS="-o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10"
SSHN="ssh -n -i $SSH_KEY $SSHOPTS"
KUBECTL="sudo kubectl --kubeconfig /etc/kubernetes/super-admin.conf"

MONITOR_PID=""
LIFTER_PID=""

# ---------------------------------------------------------------------------
# Cleanup (always runs on exit)
# ---------------------------------------------------------------------------
cleanup() {
    [[ -n "$MONITOR_PID" ]] && kill "$MONITOR_PID" 2>/dev/null || true
    [[ -n "$LIFTER_PID"  ]] && kill "$LIFTER_PID"  2>/dev/null || true
    echo ""
    echo "=== Removing test workload from cluster ==="
    $SSHN "$CP_HOST" "$KUBECTL delete deployment pdb-test-app -n default --ignore-not-found=true" 2>/dev/null || true
    $SSHN "$CP_HOST" "$KUBECTL delete pdb pdb-test -n default --ignore-not-found=true"            2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo "======================================================================"
echo "  PDB Upgrade Strategy Test"
echo "  strategy              : $STRATEGY"
echo "  upgrade_node_concurrency: $CONCURRENCY   (both strategies)"
echo "  PDB hold after cordon : ${PDB_HOLD_SECONDS}s"
echo "  target kube_version   : $KUBE_VERSION"
echo "  logs → $UPGRADE_LOG  /  $MONITOR_LOG"
echo "======================================================================"

# ---------------------------------------------------------------------------
# 1.  Verify all nodes are at the expected baseline
# ---------------------------------------------------------------------------
echo ""
echo "--- [1/5] Checking baseline (expect v1.34.4 on all nodes) ---"
NODES=$($SSHN "$CP_HOST" \
    "$KUBECTL get nodes --no-headers \
        -o custom-columns=NAME:.metadata.name,VER:.status.nodeInfo.kubeletVersion" 2>/dev/null)
echo "$NODES"
if echo "$NODES" | grep -v "v1.34.4" | grep -qE "^k8s-"; then
    echo ""
    echo "ERROR: One or more nodes are not at v1.34.4."
    echo "       Run  'vagrant destroy -f && vagrant up'  and retry."
    exit 1
fi

# ---------------------------------------------------------------------------
# 2.  Deploy nginx + PDB on k8s-4
# ---------------------------------------------------------------------------
echo ""
echo "--- [2/5] Deploying nginx + PDB on k8s-4 ---"
# scp the manifest to the control-plane node first (SSHN uses -n which blocks stdin)
scp -i "$SSH_KEY" $SSHOPTS "$MANIFEST" "${CP_HOST}:/tmp/pdb-test-manifest.yml"
$SSHN "$CP_HOST" "$KUBECTL apply -f /tmp/pdb-test-manifest.yml"

# Wait until the pod is Running on k8s-4 (up to 3 min for image pull)
echo "    Waiting for pod Running on k8s-4 (up to 3 min)..."
for i in $(seq 1 36); do
    PHASE=$($SSHN "$CP_HOST" \
        "$KUBECTL get pods -l app.kubernetes.io/name=pdb-test-app \
            -o jsonpath='{.items[0].status.phase}'" 2>/dev/null || true)
    NODE_POD=$($SSHN "$CP_HOST" \
        "$KUBECTL get pods -l app.kubernetes.io/name=pdb-test-app \
            -o jsonpath='{.items[0].spec.nodeName}'" 2>/dev/null || true)
    printf "    attempt %2d/36: phase=%-10s node=%s\n" "$i" "${PHASE:-<pending>}" "${NODE_POD:-<unset>}"
    if [[ "$PHASE" == "Running" && "$NODE_POD" == "k8s-4" ]]; then
        echo "    Pod is Running on k8s-4. PDB is active."
        break
    fi
    if [[ $i -eq 36 ]]; then
        echo "ERROR: Pod did not become Running on k8s-4 within 3 minutes."
        echo "       Check image pull:  kubectl describe pod -l app.kubernetes.io/name=pdb-test-app"
        exit 1
    fi
    sleep 5
done

# Verify the PDB is actually blocking eviction
echo "    Verifying PDB..."
$SSHN "$CP_HOST" "$KUBECTL get pdb pdb-test -n default" 2>/dev/null

# ---------------------------------------------------------------------------
# 3.  Start node monitor (5-second snapshots → $MONITOR_LOG)
# ---------------------------------------------------------------------------
echo ""
echo "--- [3/5] Starting node monitor ---"
> "$MONITOR_LOG"
(
    while true; do
        TS=$(date +%H:%M:%S)
        S=$($SSHN "$CP_HOST" \
            "$KUBECTL get nodes --no-headers \
                -o custom-columns=\
NAME:.metadata.name,\
VER:.status.nodeInfo.kubeletVersion,\
SCHED:.spec.unschedulable" 2>/dev/null) || true
        if [[ -n "$S" ]]; then
            { echo "[$TS]"; echo "$S"; echo; } >> "$MONITOR_LOG"
        fi
        sleep 5
    done
) &
MONITOR_PID=$!
echo "    Monitor PID: $MONITOR_PID  →  $MONITOR_LOG"

# ---------------------------------------------------------------------------
# 4.  Start PDB lifter
#     Waits for k8s-4 to become cordoned, then sleeps PDB_HOLD_SECONDS,
#     then deletes the PDB so kubectl drain can proceed.
# ---------------------------------------------------------------------------
echo ""
echo "--- [4/5] Starting PDB lifter (fires ${PDB_HOLD_SECONDS}s after k8s-4 is cordoned) ---"
(
    while true; do
        SCHED=$($SSHN "$CP_HOST" \
            "$KUBECTL get node k8s-4 -o jsonpath='{.spec.unschedulable}'" 2>/dev/null || true)
        if [[ "$SCHED" == "true" ]]; then
            echo "[$(date +%H:%M:%S)] PDB-LIFTER: k8s-4 cordoned — holding PDB for ${PDB_HOLD_SECONDS}s" \
                | tee -a "$UPGRADE_LOG"
            sleep "$PDB_HOLD_SECONDS"
            echo "[$(date +%H:%M:%S)] PDB-LIFTER: *** DELETING PDB — drain of k8s-4 will now succeed ***" \
                | tee -a "$UPGRADE_LOG"
            $SSHN "$CP_HOST" \
                "$KUBECTL delete pdb pdb-test -n default --ignore-not-found" \
                2>&1 | tee -a "$UPGRADE_LOG"
            echo "[$(date +%H:%M:%S)] PDB-LIFTER: PDB deleted" | tee -a "$UPGRADE_LOG"
            break
        fi
        sleep 5
    done
) &
LIFTER_PID=$!
echo "    Lifter PID: $LIFTER_PID"

# ---------------------------------------------------------------------------
# 5.  Run upgrade
# ---------------------------------------------------------------------------
echo ""
echo "--- [5/5] Running upgrade (strategy=$STRATEGY, concurrency=$CONCURRENCY) ---"
echo "[$(date +%H:%M:%S)] === UPGRADE START ===" | tee "$UPGRADE_LOG"

source "$REPO_ROOT/.venv/bin/activate"
ansible-playbook "$REPO_ROOT/playbooks/upgrade_cluster.yml" \
    -i "$INVENTORY" \
    -e kube_version="$KUBE_VERSION" \
    -e upgrade_strategy="$STRATEGY" \
    -e upgrade_node_concurrency="$CONCURRENCY" \
    -e '{"kubeadm_ignore_preflight_errors":["CreateJob"]}' \
    -b 2>&1 | tee -a "$UPGRADE_LOG"

UPGRADE_EXIT=$?
echo "[$(date +%H:%M:%S)] === UPGRADE END: exit=$UPGRADE_EXIT ===" | tee -a "$UPGRADE_LOG"

# ---------------------------------------------------------------------------
# Result analysis
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  RESULTS — strategy: $STRATEGY"
echo "======================================================================"

echo ""
echo "Worker node event timeline (cordon / version change / uncordon):"
awk '
/^\[/         { ts = $0 }
/k8s-[456]/   { print ts, $0 }
' "$MONITOR_LOG" | awk '
# Print lines where schedulable column changed or version changed
{
    key = $2          # node name
    ver = $3
    sched = $4
    sig = ver " " sched
    if (sig != prev[key]) {
        print
        prev[key] = sig
    }
}' 2>/dev/null || \
    awk '/^\[/ { ts=$0 } /k8s-[456].*true|k8s-[456].*v1\.35/ { print ts, $0 }' "$MONITOR_LOG"

echo ""
echo "PDB lifter events:"
grep "PDB-LIFTER" "$UPGRADE_LOG" || echo "  (no PDB-LIFTER entries found)"

echo ""
echo "Key timestamps:"
grep -E "UPGRADE START|UPGRADE END|PDB-LIFTER" "$UPGRADE_LOG" | sed 's/^/  /'

echo ""
echo "PLAY RECAP:"
grep -A 10 "^PLAY RECAP" "$UPGRADE_LOG" | head -12

echo ""
echo "Full logs:"
echo "  Upgrade : $UPGRADE_LOG"
echo "  Monitor : $MONITOR_LOG"

exit "$UPGRADE_EXIT"
