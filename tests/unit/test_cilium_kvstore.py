#!/usr/bin/env python
"""Regression tests for Cilium kvstore (external etcd) support.

Covers https://github.com/kubernetes-sigs/kubespray/issues/13684: since the
Helm migration, `cilium_identity_allocation_mode: kvstore` rendered
`identityAllocationMode: kvstore` without any etcd backend configuration and
without creating the `cilium-etcd-secrets` Secret, so Cilium could not reach
etcd.

Ansible is not required to run these tests. The Helm values template is
rendered with a Jinja2 environment that emulates the handful of Ansible
filters it uses; the task files are checked by parsing their YAML.
"""

import json
from pathlib import Path
from urllib.parse import urlsplit as _urlsplit

import pytest
import yaml
from jinja2 import Environment

REPO_ROOT = Path(__file__).resolve().parents[2]
CILIUM_ROLE = REPO_ROOT / "roles" / "network_plugin" / "cilium"
VALUES_TEMPLATE = CILIUM_ROLE / "templates" / "values.yaml.j2"
INSTALL_TASKS = CILIUM_ROLE / "tasks" / "install.yml"
APPLY_TASKS = CILIUM_ROLE / "tasks" / "apply.yml"
MAIN_TASKS = CILIUM_ROLE / "tasks" / "main.yml"

ETCD_ENDPOINTS = [
    "https://10.0.0.1:2379",
    "https://10.0.0.2:2379",
    "https://10.0.0.3:2379",
]


# --- Minimal emulation of the Ansible filters used by values.yaml.j2 ---------

def _to_json(value):
    return json.dumps(value)


def _to_nice_yaml(value, indent=2):
    return yaml.dump(value, indent=indent, default_flow_style=False,
                     allow_unicode=True)


def _to_yaml(value):
    return yaml.dump(value, default_flow_style=False, allow_unicode=True)


def _urlsplit_filter(value, part):
    return getattr(_urlsplit(value), part)


def _version(value, other, op):
    def parse(v):
        return tuple(int(x) for x in str(v).split("."))
    a, b = parse(value), parse(other)
    return {
        ">=": a >= b, ">": a > b, "<": a < b,
        "<=": a <= b, "==": a == b, "!=": a != b,
    }[op]


def _jinja_env():
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    env.filters["to_json"] = _to_json
    env.filters["to_nice_yaml"] = _to_nice_yaml
    env.filters["to_yaml"] = _to_yaml
    env.filters["urlsplit"] = _urlsplit_filter
    # In Ansible `cilium_version is version(...)` is a Jinja *test*.
    env.tests["version"] = _version
    return env


def _base_context(mode):
    """A complete context for values.yaml.j2 with dummy-but-valid values."""
    return {
        "cilium_identity_allocation_mode": mode,
        "etcd_access_addresses": ",".join(ETCD_ENDPOINTS),
        "_kube_apiserver_cluster_internal_endpoint": "https://127.0.0.1:6443",
        "cilium_mtu": "0",
        "cilium_debug": False,
        "cilium_image_repo": "quay.io/cilium/cilium",
        "cilium_image_tag": "v1.19.1",
        "cilium_enable_ipv4": True,
        "cilium_enable_ipv6": False,
        "cilium_l2announcements": False,
        "cilium_enable_bgp_control_plane": False,
        "cilium_agent_health_port": "9879",
        "cilium_tunnel_mode": "vxlan",
        "cilium_loadbalancer_mode": "snat",
        "cilium_kube_proxy_replacement": False,
        "cilium_agent_extra_volumes": [],
        "cilium_agent_extra_volume_mounts": [],
        "cilium_agent_extra_args": [],
        "cilium_enable_bpf_masquerade": False,
        "cilium_enable_host_legacy_routing": False,
        "cilium_monitor_aggregation": "medium",
        "cilium_preallocate_bpf_maps": False,
        "cilium_bpf_map_dynamic_size_ratio": "0.0025",
        "cilium_cni_exclusive": True,
        "cilium_cni_log_file": "/var/run/cilium/cilium-cni.log",
        "cilium_enable_portmap": False,
        "cilium_auto_direct_node_routes": False,
        "cilium_native_routing_cidr": "",
        "cilium_native_routing_cidr_ipv6": "",
        "cilium_encryption_enabled": False,
        "cilium_encryption_type": "ipsec",
        "cilium_encryption_node_encryption": False,
        "cilium_enable_bandwidth_manager": False,
        "cilium_enable_bandwidth_manager_bbr": False,
        "cilium_ip_masq_agent_enable": False,
        "cilium_non_masquerade_cidrs": ["10.0.0.0/8"],
        "cilium_masq_link_local": False,
        "cilium_masq_link_local_ipv6": False,
        "cilium_hubble_peer_service_cluster_domain": "cluster.local",
        "cilium_enable_hubble": False,
        "cilium_hubble_relay_image_repo": "quay.io/cilium/hubble-relay",
        "cilium_hubble_relay_image_tag": "v1.19.1",
        "cilium_enable_hubble_ui": False,
        "cilium_hubble_ui_backend_image_repo": "quay.io/cilium/hubble-ui-backend",
        "cilium_hubble_ui_backend_image_tag": "v0.13.0",
        "cilium_hubble_ui_image_repo": "quay.io/cilium/hubble-ui",
        "cilium_hubble_ui_image_tag": "v0.13.0",
        "cilium_hubble_metrics": [],
        "cilium_hubble_scrape_port": "9965",
        "cilium_version": "1.19.1",
        "cilium_hubble_export_file_max_backups": "5",
        "cilium_hubble_export_file_max_size_mb": "10",
        "cilium_hubble_export_dynamic_enabled": False,
        "cilium_hubble_export_dynamic_config_content": [{"name": "all"}],
        "cilium_gateway_api_enabled": False,
        "cilium_ipam_mode": "cluster-pool",
        "kube_pods_subnet": "10.233.64.0/18",
        "kube_network_node_prefix": 24,
        "kube_pods_subnet_ipv6": "fd85:ee78:d8a6:8607::1:0000/112",
        "kube_network_node_prefix_ipv6": 120,
        "cilium_cgroup_auto_mount": True,
        "cilium_cgroup_host_root": "/run/cilium/cgroupv2",
        "cilium_memory_limit": "500M",
        "cilium_cpu_limit": "500m",
        "cilium_memory_requests": "64M",
        "cilium_cpu_requests": "100m",
        "cilium_operator_image_repo": "quay.io/cilium/operator",
        "cilium_operator_image_tag": "v1.19.1",
        "cilium_operator_replicas": 2,
        "cilium_operator_scrape_port": "9963",
        "cilium_operator_extra_args": [],
        "cilium_operator_extra_volumes": [],
        "cilium_operator_extra_volume_mounts": [],
        "cilium_operator_tolerations": [{"operator": "Exists"}],
        "cilium_cluster_id": 0,
        "cilium_cluster_name": "default",
        "cilium_enable_ipv4_masquerade": True,
        "cilium_enable_ipv6_masquerade": True,
        "cilium_enable_host_firewall": False,
        "cilium_policy_audit_mode": False,
        "cilium_enable_prometheus": False,
        "cilium_agent_scrape_port": "9962",
        "cilium_certgen_image_repo": "quay.io/cilium/certgen",
        "cilium_certgen_image_tag": "v0.1.0",
        "cilium_envoy_image_repo": "quay.io/cilium/cilium-envoy",
        "cilium_envoy_image_tag": "v1.30.0",
        "cilium_config_extra_vars": {},
        "cilium_extra_values": {},
    }


def render_values(mode, extra_values=None):
    context = _base_context(mode)
    if extra_values is not None:
        context["cilium_extra_values"] = extra_values
    env = _jinja_env()
    template = env.from_string(VALUES_TEMPLATE.read_text())
    return template.render(**context)


def load_tasks(path):
    return yaml.safe_load(path.read_text())


def iter_task_names(tasks):
    return [t.get("name", "") for t in tasks]


# --- A. CRD configuration rendering ------------------------------------------

def test_crd_render_is_valid_yaml_without_etcd():
    rendered = render_values("crd")
    parsed = yaml.safe_load(rendered)  # must parse
    assert parsed["identityAllocationMode"] == "crd"
    # crd mode must not introduce any etcd backend configuration
    assert "etcd" not in parsed


# --- B. Kvstore configuration rendering --------------------------------------

def test_kvstore_render_configures_etcd():
    rendered = render_values("kvstore")
    parsed = yaml.safe_load(rendered)  # resulting YAML must parse
    assert parsed["identityAllocationMode"] == "kvstore"
    etcd = parsed["etcd"]
    assert etcd["enabled"] is True
    assert etcd["ssl"] is True
    # endpoints follow etcd_access_addresses, in order
    assert etcd["endpoints"] == ETCD_ENDPOINTS


# --- Backward compatibility: user-managed etcd via cilium_extra_values --------

def test_manual_etcd_in_extra_values_disables_kubespray_etcd_block():
    # When the user configures etcd themselves through cilium_extra_values,
    # Kubespray must NOT render its own etcd block (their cilium-extra-values.yaml
    # provides it instead), so we never fight their configuration.
    rendered = render_values("kvstore", extra_values={"etcd": {"enabled": True}})
    parsed = yaml.safe_load(rendered)
    assert parsed["identityAllocationMode"] == "kvstore"
    assert "etcd" not in parsed


# --- C. Secret behavior -------------------------------------------------------

def _secret_generate_task(tasks):
    for t in tasks:
        cmd = t.get("command")
        if isinstance(cmd, str) and "create secret generic cilium-etcd-secrets" in cmd:
            return t
    return None


def _secret_apply_task(tasks):
    for t in tasks:
        cmd = t.get("command")
        if isinstance(cmd, dict) and "apply -f -" in cmd.get("cmd", ""):
            return t
    return None


def test_secret_name_namespace_and_keys():
    tasks = load_tasks(INSTALL_TASKS)
    gen = _secret_generate_task(tasks)
    assert gen is not None, "cilium-etcd-secrets generate task not found"
    cmd = gen["command"]
    assert "--namespace kube-system" in cmd
    assert "--from-file=etcd-client-ca.crt=" in cmd
    assert "--from-file=etcd-client.crt=" in cmd
    assert "--from-file=etcd-client.key=" in cmd


def _all_secret_tasks(tasks):
    """Every task that touches the Kubespray-managed Secret / its certs."""
    out = []
    for t in tasks:
        name = t.get("name", "")
        if ("cilium-etcd-secrets" in name
                or "etcd client certificates" in name
                or t is _secret_generate_task(tasks)
                or t is _secret_apply_task(tasks)):
            out.append(t)
    return out


def test_secret_tasks_run_only_for_kvstore():
    tasks = load_tasks(INSTALL_TASKS)
    for task in (_secret_generate_task(tasks), _secret_apply_task(tasks)):
        assert task is not None
        when = task.get("when", [])
        assert 'cilium_identity_allocation_mode == "kvstore"' in when


def test_secret_tasks_skipped_when_user_manages_etcd():
    # Backward compatibility: with an etcd key in cilium_extra_values, every
    # Secret/cert task must be guarded so Kubespray does not overwrite a
    # user-managed cilium-etcd-secrets or fail on absent managed certs.
    tasks = load_tasks(INSTALL_TASKS)
    guarded = _all_secret_tasks(tasks)
    assert guarded, "expected Secret/cert management tasks"
    for task in guarded:
        when = task.get("when", [])
        assert "'etcd' not in cilium_extra_values" in when, (
            f"task {task.get('name')!r} missing the cilium_extra_values guard"
        )


def test_secret_tasks_do_not_log_secret_material():
    tasks = load_tasks(INSTALL_TASKS)
    for task in (_secret_generate_task(tasks), _secret_apply_task(tasks)):
        assert task is not None
        assert task.get("no_log") is True


def test_missing_certificate_files_fail_clearly():
    tasks = load_tasks(INSTALL_TASKS)
    # a stat task gathers the cert files, an assert task fails when absent
    stat_task = next((t for t in tasks if "stat" in t), None)
    assert_task = next((t for t in tasks if "assert" in t), None)
    assert stat_task is not None, "expected a stat task for etcd cert files"
    assert assert_task is not None, "expected an assert task for missing certs"
    assert assert_task["assert"]["that"] == "item.stat.exists"
    assert "fail_msg" in assert_task["assert"]


def test_secret_applied_with_kubectl_apply_not_create():
    # Structural check only: it asserts the Secret is written with `kubectl
    # apply` (not a one-shot `create`), which is what makes repeated runs and
    # cert updates safe. It does NOT prove runtime idempotency; that needs a
    # live cluster.
    tasks = load_tasks(INSTALL_TASKS)
    apply_task = _secret_apply_task(tasks)
    assert apply_task is not None
    assert "apply -f -" in apply_task["command"]["cmd"]


def test_no_cilium_cert_dir_or_certificate_linking_left():
    # Requirement 3: the obsolete /etc/cilium/certs hard-link tasks are gone.
    install_text = INSTALL_TASKS.read_text()
    assert "cilium_cert_dir" not in install_text
    assert "Link etcd certificates" not in install_text


# --- D. Execution ordering ----------------------------------------------------

def test_secret_created_before_cilium_install():
    # The Helm install/upgrade lives in apply.yml; the Secret is created in
    # install.yml; main.yml runs install before apply. Together this guarantees
    # the Secret exists before Cilium consumes it.
    install_tasks = load_tasks(INSTALL_TASKS)
    apply_tasks = load_tasks(APPLY_TASKS)

    assert _secret_generate_task(install_tasks) is not None
    assert _secret_apply_task(install_tasks) is not None

    helm_task = next(
        (t for t in apply_tasks
         if isinstance(t.get("command"), str)
         and "cilium" in t["command"] and "{{ cilium_action }}" in t["command"]),
        None,
    )
    assert helm_task is not None, "Helm install/upgrade task not found in apply.yml"

    main_text = MAIN_TASKS.read_text()
    assert main_text.index("install.yml") < main_text.index("apply.yml")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
