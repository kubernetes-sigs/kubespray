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

## ~~Fix 4: Improve nginx-proxy node targeting~~ [INCORRECT - DO NOT USE]

**File:** `roles/kubernetes/node/tasks/main.yml`
**Status:** ❌ **THIS FIX IS INCORRECT AND SHOULD NOT BE APPLIED**
**Issue:** Custom nginx-proxy targeting causes port conflicts and deployment failures
**Impact:** Leads to API server startup failures and circular dependencies

```yaml
# Original kubespray logic (KEEP THIS):
- name: Install nginx-proxy
  import_tasks: loadbalancer/nginx-proxy.yml
  when:
    - ('kube_control_plane' not in group_names) or (kube_apiserver_bind_address != '::')
    - loadbalancer_apiserver_localhost
    - loadbalancer_apiserver_type == 'nginx'

# INCORRECT modification (DO NOT USE):
- name: Install nginx-proxy
  import_tasks: loadbalancer/nginx-proxy.yml
  when:
    - inventory_hostname == 'node1'  # WRONG - causes conflicts
    - loadbalancer_apiserver_localhost
    - loadbalancer_apiserver_type == 'nginx'
```

**Problem Analysis:**
- nginx-proxy binds to port 6443, conflicting with API server
- Creates circular dependency preventing proper cluster initialization  
- Original kubespray logic is correct for most deployments
- Custom targeting should only be done if absolutely necessary and with different ports

**Recommendation:** Use kubespray's default nginx-proxy configuration

## Testing

Fixes 1-3 have been tested on:
- Ubuntu systems with modern kernels
- Various container runtime configurations  
- Multi-node cluster deployments

**Fix 4 was determined to be incorrect and should not be applied.**

## Impact

**Valid Fixes (1-3):**
- Fixes module loading failures on modern systems (Fix 1)
- Prevents container runtime startup failures (Fixes 2-3)
- Maintains backward compatibility
- All valid fixes preserve existing functionality while handling edge cases

**Invalid Fix (4):**
- Creates port conflicts and circular dependencies
- Breaks API server initialization
- Should be avoided - use kubespray defaults instead

## Summary

**Apply:** Fixes 1, 2, and 3 only  
**Avoid:** Fix 4 (nginx-proxy targeting)