#!/usr/bin/env bash
# tests/scripts/monitor-upgrade.sh
#
# Continuously records the cordon/drain state of all cluster nodes during an
# upgrade run and writes a timestamped log.  Run this in a SEPARATE terminal
# BEFORE starting the upgrade playbook.
#
# Usage (local kubectl):
#   export KUBECONFIG=.vagrant/provisioners/ansible/inventory/artifacts/admin.conf
#   bash tests/scripts/monitor-upgrade.sh            # logs to /tmp/node-states.log
#   bash tests/scripts/monitor-upgrade.sh myrun.log  # custom log file
#
# Usage (remote — kubectl runs on control-plane node via ansible):
#   export REMOTE_NODE=k8s-1
#   export REMOTE_INVENTORY=.vagrant/provisioners/ansible/inventory
#   export REMOTE_VENV=/path/to/kubespray/.venv          # optional
#   export REMOTE_KUBECONFIG=/etc/kubernetes/super-admin.conf  # optional
#   bash tests/scripts/monitor-upgrade.sh myrun.log
#
# After the upgrade finishes, press Ctrl+C to stop the monitor, then run:
#   bash tests/scripts/monitor-upgrade.sh --report myrun.log
# to see a summary of peak concurrency and timeline.

set -euo pipefail

LOGFILE="${1:-/tmp/node-states.log}"
INTERVAL="${INTERVAL:-3}"  # seconds between polls

# ── Colour codes (disabled when stdout is not a terminal) ─────────────────────
if [[ -t 1 ]]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

# ── Report mode ───────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--report" ]]; then
  LOGFILE="${2:-/tmp/node-states.log}"
  if [[ ! -f "$LOGFILE" ]]; then
    echo "ERROR: log file not found: $LOGFILE" >&2
    exit 1
  fi

  echo "=== Upgrade monitoring report: $LOGFILE ==="
  echo ""

  # Parse peak from summary lines: [TS] total=N ready=N not_ready=N disabled=N
  echo "--- Peak concurrent SchedulingDisabled nodes ---"
  awk '
    /\[.*\] total=/ && match($0, /disabled=([0-9]+)/, a) && a[1]+0 > 0 {
      print $0
    }
  ' "$LOGFILE"

  echo ""
  echo "--- All cordon events (node + timestamp) ---"
  grep -B5 "CORDONED" "$LOGFILE" | grep -E "^=== |CORDONED" || true

  echo ""
  echo "--- Max simultaneous cordoned ---"
  awk '
    match($0, /disabled=([0-9]+)/, a) { n=a[1]+0; if (n>max) max=n }
    END { print max+0 " node(s)" }
  ' "$LOGFILE"
  exit 0
fi

# ── Monitor mode ──────────────────────────────────────────────────────────────

# _kubectl: run kubectl locally or via ansible on REMOTE_NODE.
# When REMOTE_NODE is set, no local KUBECONFIG is needed.
_kubectl() {
  if [[ -n "${REMOTE_NODE:-}" ]]; then
    local inv="${REMOTE_INVENTORY:-.vagrant/provisioners/ansible/inventory}"
    local ab="${REMOTE_VENV:+${REMOTE_VENV}/bin/}ansible"
    local kc="${REMOTE_KUBECONFIG:-/etc/kubernetes/super-admin.conf}"
    "${ab}" "${REMOTE_NODE}" -i "${inv}" -m shell \
      -a "kubectl --kubeconfig '${kc}' $* 2>/dev/null" -b 2>/dev/null \
      | grep -v "^[^ ]* | [A-Z]"
    return "${PIPESTATUS[0]}"
  else
    command kubectl "$@"
  fi
}

if [[ -z "${REMOTE_NODE:-}" ]]; then
  if [[ -z "${KUBECONFIG:-}" ]]; then
    # Resolve path relative to the script's own location so this script can be
    # run from any directory (not just the kubespray repo root).
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    CANDIDATE="${REPO_ROOT}/.vagrant/provisioners/ansible/inventory/artifacts/admin.conf"
    if [[ -f "$CANDIDATE" ]]; then
      export KUBECONFIG="$CANDIDATE"
      echo "INFO: using KUBECONFIG=$KUBECONFIG"
    else
      echo "ERROR: KUBECONFIG is not set and $CANDIDATE does not exist." >&2
      echo "       Run: export KUBECONFIG=<path-to-admin.conf>" >&2
      echo "       Or:  export REMOTE_NODE=k8s-1 REMOTE_INVENTORY=<path> REMOTE_VENV=<path>" >&2
      exit 1
    fi
  fi
fi

# Verify kubectl is reachable (local or remote)
if ! _kubectl get nodes &>/dev/null; then
  echo "ERROR: kubectl cannot reach the cluster. Check KUBECONFIG/REMOTE_NODE and connectivity." >&2
  exit 1
fi

echo "Monitoring started — logging to: $LOGFILE"
echo "Press Ctrl+C to stop."
echo ""

# Header line: remind which metric matters for the comparison
echo -e "${BOLD}Watch 'disabled=N': graceful_rolling shows N≤concurrency with no gaps;${RESET}"
echo -e "${BOLD}linear(serial:20%) shows N=1 until entire batch finishes.${RESET}"
echo ""

# Truncate / start fresh
: > "$LOGFILE"

# Track previous disabled count so we can annotate rises/falls
prev_disabled=-1

while true; do
  TS=$(date "+%Y-%m-%d %H:%M:%S")
  disabled=0; ready=0; not_ready=0; total=0
  disabled_names=()

  # Parse node states — default output: NAME STATUS ROLES AGE VERSION
  # STATUS is e.g. "Ready", "NotReady", "Ready,SchedulingDisabled"
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    name="$(awk '{print $1}' <<< "$line")"
    status="$(awk '{print $2}' <<< "$line")"
    (( total++ )) || true
    if [[ "$status" == *"SchedulingDisabled"* ]]; then
      (( disabled++ )) || true
      disabled_names+=("$name")
    fi
    if [[ "$status" == *"NotReady"* ]]; then (( not_ready++ )) || true
    else (( ready++ )) || true; fi
  done < <(_kubectl get nodes --no-headers 2>/dev/null)

  # Colour by count: 0=green, 1=yellow, ≥2=red
  if   (( disabled == 0 )); then c="$GREEN"
  elif (( disabled == 1 )); then c="$YELLOW"
  else                           c="$RED"; fi

  # Annotation for slot events
  annotation=""
  if   (( prev_disabled >= 0 && disabled > prev_disabled )); then annotation=" ↑ upgrade started"
  elif (( prev_disabled >= 0 && disabled < prev_disabled )); then annotation=" ↓ slot freed"; fi
  prev_disabled=$disabled

  names_str=""
  if (( ${#disabled_names[@]} > 0 )); then
    names_str=" [$(IFS=,; echo "${disabled_names[*]}")]"
  fi

  # One-liner summary (also written to log without ANSI codes)
  summary="${c}[${TS}] total=${total} ready=${ready} not_ready=${not_ready} disabled=${disabled}${names_str}${annotation}${RESET}"
  echo -e "$summary"
  echo "[${TS}] total=${total} ready=${ready} not_ready=${not_ready} disabled=${disabled}${names_str}${annotation}" >> "$LOGFILE"

  {
    echo "=== $TS ==="
    _kubectl get nodes --no-headers 2>/dev/null \
      | awk '{
          sched  = ($2 ~ /SchedulingDisabled/) ? "CORDONED" : "schedulable"
          ready  = ($2 ~ /NotReady/)           ? "False"    : "True"
          printf "  %-20s  ready=%-5s  %-12s  %s\n", $1, ready, sched, $5
        }'
    echo "---"
  } >> "$LOGFILE"

  sleep "$INTERVAL"
done
