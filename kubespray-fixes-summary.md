# Kubespray v2.28.0 Bug Fixes

This document summarizes fixes for several deployment issues found in Kubespray v2.28.0.

## Fix 1: Remove deprecated nf_conntrack_ipv4 module

**File:** `roles/kubernetes/node/defaults/main.yml`
**Issue:** nf_conntrack_ipv4 module is deprecated and merged into nf_conntrack in newer kernels
**Impact:** Module loading failures on modern systems

```yaml
# Before (line 189):
conntrack_modules:
  - nf_conntrack
  - nf_conntrack_ipv4

# After:
conntrack_modules:
  - nf_conntrack
  # - nf_conntrack_ipv4  # deprecated, merged into nf_conntrack
```

## Fix 2: Add conditionals to containerd runtime templates

**Files:** 
- `roles/container-engine/containerd/templates/config.toml.j2`
- `roles/container-engine/containerd/templates/config-v1.toml.j2`

**Issue:** Empty runtime.engine and runtime.root values cause containerd config failures
**Impact:** Containerd fails to start with invalid configuration

### config.toml.j2
```jinja2
# Before (lines 46-47):
         runtime_engine = "{{ runtime.engine }}"
         runtime_root = "{{ runtime.root }}"

# After:
{% if runtime.engine is defined and runtime.engine != "" %}
         runtime_engine = "{{ runtime.engine }}"
{% endif %}
{% if runtime.root is defined and runtime.root != "" %}
         runtime_root = "{{ runtime.root }}"
{% endif %}
```

### config-v1.toml.j2
```jinja2
# Before (lines 50-51):
          runtime_engine = "{{ runtime.engine }}"
          runtime_root = "{{ runtime.root }}"

# After:
{% if runtime.engine is defined and runtime.engine != "" %}
          runtime_engine = "{{ runtime.engine }}"
{% endif %}
{% if runtime.root is defined and runtime.root != "" %}
          runtime_root = "{{ runtime.root }}"
{% endif %}
```

## Fix 3: Add conditional to CRI-O runtime template

**File:** `roles/container-engine/cri-o/templates/crio.conf.j2`
**Issue:** Empty runtime.root values cause CRI-O config failures
**Impact:** CRI-O fails to start with invalid configuration

```ini
# Before (line 298):
runtime_root = "{{ runtime.root }}"

# After:
{% if runtime.root is defined and runtime.root != "" %}
runtime_root = "{{ runtime.root }}"
{% endif %}
```

## ~~Fix 4: nginx-proxy node targeting~~ [INCORRECT - DO NOT USE]

**File:** `roles/kubernetes/node/tasks/main.yml`  
**Status:** ❌ **THIS FIX IS INCORRECT AND SHOULD NOT BE APPLIED**
**Issue:** Misunderstands nginx-proxy architecture and purpose
**Impact:** Breaks nginx-proxy's intended function as local API proxy

```yaml
# Original kubespray logic (CORRECT - keep this):
- name: Install nginx-proxy
  import_tasks: loadbalancer/nginx-proxy.yml
  when:
    - ('kube_control_plane' not in group_names) or (kube_apiserver_bind_address != '::')
    - loadbalancer_apiserver_localhost
    - loadbalancer_apiserver_type == 'nginx'

# WRONG modification (DO NOT USE):
- name: Install nginx-proxy
  import_tasks: loadbalancer/nginx-proxy.yml
  when:
    - inventory_hostname == 'specific_node'  # BREAKS the design
    - loadbalancer_apiserver_localhost
    - loadbalancer_apiserver_type == 'nginx'
```

**Why this fix is wrong:**
- nginx-proxy is designed to run on **worker nodes** for localhost:6443 forwarding
- It provides local API access for kubelet and services on worker nodes
- Control plane nodes already have direct API server access
- Custom targeting breaks this architectural pattern

**Correct approach:** Use kubespray's default nginx-proxy targeting logic

## Testing

**Fixes 1-3 have been tested on:**
- Ubuntu systems with modern kernels
- Various container runtime configurations  
- Multi-node cluster deployments

**Fix 4 was determined to be architecturally incorrect.**

## Impact

**Valid Fixes (1-3):**
- Fixes module loading failures on modern systems (Fix 1)
- Prevents container runtime startup failures (Fixes 2-3)
- Safe to apply to any kubespray deployment
- Maintains backward compatibility

**Invalid Fix (4):**
- Misunderstands nginx-proxy's role as local API proxy for worker nodes
- Breaks kubespray's intended architecture
- Can cause API access issues for worker node components
- **DO NOT APPLY** - use kubespray defaults instead

## Summary

**Apply:** Fixes 1, 2, and 3 only  
**Avoid:** Fix 4 (nginx-proxy targeting)  
**Recommendation:** Always use kubespray's default nginx-proxy configuration