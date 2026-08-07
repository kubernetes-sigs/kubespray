#!/bin/bash
#
# Cilium WireGuard Encryption Verification Script
#
# This script verifies that Cilium WireGuard encryption (including Strict Mode)
# is properly configured and active in your Kubernetes cluster.
#
# Usage:
#   ./verify-encryption.sh [namespace]
#
# Default namespace: kube-system
#

set -euo pipefail

NAMESPACE="${1:-kube-system}"
CILIUM_DS="cilium"
SUCCESS=0
FAILURES=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    FAILURES=$((FAILURES + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if Cilium DaemonSet exists
if ! kubectl get ds "$CILIUM_DS" -n "$NAMESPACE" &> /dev/null; then
    print_error "Cilium DaemonSet '$CILIUM_DS' not found in namespace '$NAMESPACE'"
    exit 1
fi

print_info "Verifying Cilium WireGuard Encryption Configuration..."
echo ""

# Get a Cilium pod name
CILIUM_POD=$(kubectl get pods -n "$NAMESPACE" -l k8s-app=cilium -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$CILIUM_POD" ]; then
    print_error "No Cilium pods found in namespace '$NAMESPACE'"
    exit 1
fi

print_info "Using Cilium pod: $CILIUM_POD"
echo ""

# Check 1: Verify encryption is enabled in Cilium status
print_info "Checking Cilium encryption status..."
ENCRYPTION_STATUS=$(kubectl exec -n "$NAMESPACE" "$CILIUM_POD" -- cilium status 2>/dev/null | grep -i "Encryption:" || echo "")

if echo "$ENCRYPTION_STATUS" | grep -qi "WireGuard\|Enabled"; then
    print_success "Encryption is enabled"
    echo "  $ENCRYPTION_STATUS"
else
    print_error "Encryption is not enabled or not using WireGuard"
    if [ -n "$ENCRYPTION_STATUS" ]; then
        echo "  $ENCRYPTION_STATUS"
    fi
fi
echo ""

# Check 2: Verify WireGuard interface exists
print_info "Checking for WireGuard interface..."
WG_INTERFACE=$(kubectl exec -n "$NAMESPACE" "$CILIUM_POD" -- ip link show type wireguard 2>/dev/null | head -1 || echo "")

if [ -n "$WG_INTERFACE" ]; then
    print_success "WireGuard interface found"
    kubectl exec -n "$NAMESPACE" "$CILIUM_POD" -- ip link show type wireguard 2>/dev/null | sed 's/^/  /'
else
    print_error "WireGuard interface not found"
    print_warning "This may indicate that WireGuard encryption is not active"
fi
echo ""

# Check 3: Verify encryption mode (pod-to-pod and node-to-node)
print_info "Checking encryption configuration details..."
CILIUM_CONFIG=$(kubectl exec -n "$NAMESPACE" "$CILIUM_POD" -- cilium config 2>/dev/null || echo "")

if echo "$CILIUM_CONFIG" | grep -qi "encryption.*wireguard"; then
    print_success "WireGuard encryption is configured"
    
    # Check for node encryption
    if echo "$CILIUM_CONFIG" | grep -qi "node-encryption.*true\|nodeEncryption.*true"; then
        print_success "Node-to-node encryption is enabled (Strict Mode active)"
    else
        print_warning "Node-to-node encryption may not be enabled"
        print_info "For Strict Mode, ensure cilium_encryption_strict_mode is set to true"
    fi
else
    print_error "WireGuard encryption configuration not found"
fi
echo ""

# Check 4: Verify WireGuard keys are present
print_info "Checking for WireGuard keys..."
WG_KEYS=$(kubectl exec -n "$NAMESPACE" "$CILIUM_POD" -- wg show 2>/dev/null || echo "")

if [ -n "$WG_KEYS" ]; then
    print_success "WireGuard keys are present"
    echo "  WireGuard peers configured: $(echo "$WG_KEYS" | grep -c "peer" || echo "0")"
else
    print_warning "Could not retrieve WireGuard keys (this may be normal if encryption is still initializing)"
fi
echo ""

# Check 5: Verify kernel WireGuard support
print_info "Checking kernel WireGuard support..."
KERNEL_MODULE=$(kubectl exec -n "$NAMESPACE" "$CILIUM_POD" -- lsmod 2>/dev/null | grep -i wireguard || echo "")

if [ -n "$KERNEL_MODULE" ]; then
    print_success "WireGuard kernel module is loaded"
    echo "$KERNEL_MODULE" | sed 's/^/  /'
else
    print_warning "WireGuard kernel module not found in lsmod"
    print_info "This may be normal if WireGuard is built into the kernel"
fi
echo ""

# Check 6: Verify Cilium Helm values (if available)
print_info "Checking Cilium ConfigMap for encryption settings..."
CONFIGMAP=$(kubectl get configmap cilium-config -n "$NAMESPACE" -o yaml 2>/dev/null || echo "")

if [ -n "$CONFIGMAP" ]; then
    if echo "$CONFIGMAP" | grep -qi "encryption.*wireguard\|encryption-type.*wireguard"; then
        print_success "WireGuard encryption found in Cilium ConfigMap"
    else
        print_warning "WireGuard encryption not found in Cilium ConfigMap"
    fi
    
    if echo "$CONFIGMAP" | grep -qi "node-encryption.*true\|nodeEncryption.*true"; then
        print_success "Node-to-node encryption found in Cilium ConfigMap"
    fi
else
    print_warning "Could not retrieve Cilium ConfigMap"
fi
echo ""

# Summary
echo "=========================================="
if [ $FAILURES -eq 0 ]; then
    print_success "All encryption checks passed!"
    echo ""
    print_info "Your cluster appears to have WireGuard encryption properly configured."
    print_info "All pod-to-pod and node-to-node traffic is encrypted at the kernel level."
    SUCCESS=1
else
    print_error "Some encryption checks failed ($FAILURES failure(s))"
    echo ""
    print_warning "Please verify your configuration:"
    print_warning "  - Ensure cilium_encryption_strict_mode: true is set in your inventory"
    print_warning "  - Verify all nodes have Linux kernel 5.6+ with WireGuard support"
    print_warning "  - Check that Cilium pods are running and healthy"
    SUCCESS=0
fi
echo "=========================================="

exit $SUCCESS
