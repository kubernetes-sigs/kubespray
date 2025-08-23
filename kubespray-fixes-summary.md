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

## Fix 4: Target nginx-proxy to internet gateway node [DEPLOYMENT-SPECIFIC]

**File:** `roles/kubernetes/node/tasks/main.yml`
**Status:** ✅ **VALID but deployment-specific - use with caution**
**Issue:** nginx-proxy may deploy to wrong node when only one node has inbound internet access
**Impact:** External API access fails if nginx-proxy deploys to non-internet-accessible node

```yaml
# Original kubespray logic:
- name: Install nginx-proxy
  import_tasks: loadbalancer/nginx-proxy.yml
  when:
    - ('kube_control_plane' not in group_names) or (kube_apiserver_bind_address != '::')
    - loadbalancer_apiserver_localhost
    - loadbalancer_apiserver_type == 'nginx'

# Targeted modification for specific network topologies:
- name: Install nginx-proxy
  import_tasks: loadbalancer/nginx-proxy.yml
  when:
    - inventory_hostname == 'node1'  # internet gateway node
    - loadbalancer_apiserver_localhost
    - loadbalancer_apiserver_type == 'nginx'
```

**Use Case:**
- **Only apply** when one specific node has inbound internet access
- nginx-proxy provides HA load balancing for external API access
- Ensures external kubectl/monitoring can reach the cluster
- Routes through designated internet gateway to internal control plane

**⚠️ Warning:** This is **deployment-specific**. Use kubespray defaults unless you have this exact network topology.

## Testing

**All fixes have been tested on:**
- Ubuntu systems with modern kernels
- Various container runtime configurations  
- Multi-node cluster deployments
- Network topologies with single internet gateway node

## Impact

**Universal Fixes (1-3):**
- Fixes module loading failures on modern systems (Fix 1)
- Prevents container runtime startup failures (Fixes 2-3)
- Safe to apply to any kubespray deployment
- Maintains backward compatibility

**Deployment-Specific Fix (4):**
- Solves external API access issues for specific network topologies
- Required when only one node has inbound internet access
- Provides HA load balancing through designated gateway
- **Only apply if you have this exact network setup**

## Summary

**Always Apply:** Fixes 1, 2, and 3 (universal)  
**Conditionally Apply:** Fix 4 (only for single internet gateway deployments)  
**Default Recommendation:** Use kubespray defaults unless you specifically need Fix 4