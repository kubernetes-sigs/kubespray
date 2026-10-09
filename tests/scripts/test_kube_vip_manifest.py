#!/usr/bin/env python3
"""Regression tests for the kube-vip static pod manifest.

Covers the BGP control-plane health check variables added for
https://github.com/kubernetes-sigs/kubespray/issues/13618.

The manifest is a plain Jinja2 template producing a Pod manifest, so it can be
rendered and parsed without Ansible. The important properties are:

* the health check is entirely opt-in: nothing is emitted when
  ``kube_vip_control_plane_health_check_address`` is unset, so existing
  deployments keep the exact same manifest;
* the health check env vars are only emitted when the address is set, matching
  kube-vip, which enables the check through that single setting;
* the rendered manifest is always valid YAML.
"""

from __future__ import annotations

import json
import pathlib

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROLE = pathlib.Path(__file__).resolve().parents[2].joinpath(
    "roles", "kubernetes", "node")
TEMPLATE = ROLE.joinpath("templates", "manifests", "kube-vip.manifest.j2")
DEFAULTS_FILE = ROLE.joinpath("defaults", "main.yml")

HEALTH_CHECK_VARS = (
    "control_plane_health_check_address",
    "control_plane_health_check_period_seconds",
    "control_plane_health_check_timeout_seconds",
    "control_plane_health_check_failure_threshold",
    "control_plane_health_check_ca_path",
)
HEALTH_CHECK_KUBESPRAY_VARS = tuple("kube_vip_" + v for v in HEALTH_CHECK_VARS)


def _to_json(value) -> str:
    """Ansible's ``to_json`` filter: JSON-encode as a single-quoted scalar.

    The manifest relies on the scalar form (``value: "foo"``), which Jinja2's
    own ``tojson`` filter does not produce.
    """
    return json.dumps(value)


def _version(value, target, operator="==", strict=False) -> bool:
    """Minimal subset of Ansible's ``version`` test, enough for the manifest.

    Ansible calls it as ``value is version(target, operator)``.
    """
    def as_tuple(text):
        parts = []
        for part in str(text).lstrip("v").split("."):
            digits = ""
            for char in part:
                if not char.isdigit():
                    break
                digits += char
            if not digits:
                break
            parts.append(int(digits))
        return tuple(parts)

    left, right = as_tuple(value), as_tuple(target)
    if strict and len(left) != len(right):
        raise ValueError("version comparison requires exact version match")
    comparisons = {
        ">=": left >= right,
        "<=": left <= right,
        ">": left > right,
        "<": left < right,
        "==": left == right,
        "!=": left != right,
    }
    if operator not in comparisons:
        raise ValueError(f"unsupported version operator: {operator!r}")
    return comparisons[operator]


def default_vars() -> dict:
    """Minimal set of variables the manifest references unconditionally."""
    return {
        "kube_vip_arp_enabled": False,
        "kube_apiserver_port": 6443,
        "inventory_hostname": "node1",
        "kube_vip_interface": None,
        "kube_vip_services_interface": None,
        "kube_vip_cidr": 32,
        "kube_vip_dns_mode": "first",
        "kube_vip_controlplane_enabled": True,
        "kube_vip_ddns_enabled": False,
        "kube_vip_cp_detect": False,
        "kube_vip_services_enabled": False,
        "kube_vip_svc_leasename": "plndr-svcs-lock",
        "kube_vip_enableServicesElection": False,
        "kube_vip_leader_election_enabled": False,
        "kube_vip_leasename": "plndr-cp-lock",
        "kube_vip_leaseduration": 5,
        "kube_vip_renewdeadline": 3,
        "kube_vip_retryperiod": 1,
        "kube_vip_enable_node_labeling": False,
        "kube_vip_bgp_enabled": False,
        "kube_vip_bgp_routerid": None,
        "kube_vip_local_as": 65000,
        "kube_vip_bgp_peeraddress": None,
        "kube_vip_bgp_peerpass": None,
        "kube_vip_bgp_peeras": 65000,
        "kube_vip_bgppeers": [],
        "kube_vip_lb_enable": False,
        "kube_vip_lb_fwdmethod": "local",
        "kube_vip_metrics_enabled": False,
        "kube_vip_metrics_port": 2112,
        "kube_vip_image_repo": "ghcr.io/kube-vip/kube-vip",
        "kube_vip_version": "1.2.4",
        "kube_vip_image_tag": "v1.2.4",
        "k8s_image_pull_policy": "IfNotPresent",
        "kube_vip_address": "10.0.0.10",
        "kube_vip_admin_conf": "admin.conf",
        "kube_vip_bgp_sourceip": None,
        "kube_vip_bgp_sourceif": None,
        # New health check variables default to unset (opt-in).
        "kube_vip_control_plane_health_check_address": None,
        "kube_vip_control_plane_health_check_period_seconds": None,
        "kube_vip_control_plane_health_check_timeout_seconds": None,
        "kube_vip_control_plane_health_check_failure_threshold": None,
        "kube_vip_control_plane_health_check_ca_path": None,
    }


def render(manifest_vars: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE.parent)),
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters["to_json"] = _to_json
    env.tests["version"] = _version
    return env.get_template(TEMPLATE.name).render(**manifest_vars)


def env_vars(rendered: str) -> dict[str, str]:
    manifest = yaml.safe_load(rendered)
    return {e["name"]: e["value"] for e in
            manifest["spec"]["containers"][0]["env"]}


def test_defaults_declare_health_check_variables() -> None:
    """Every new variable must exist in the role defaults, unset by default."""
    defaults = yaml.safe_load(DEFAULTS_FILE.read_text())
    for var in HEALTH_CHECK_KUBESPRAY_VARS:
        assert var in defaults, f"{var} missing from role defaults"
        assert not defaults[var], (
            f"{var} must default to unset so the health check stays opt-in")


def test_health_check_disabled_by_default() -> None:
    """The default manifest must not contain any health check env var."""
    env = env_vars(render(default_vars()))
    for var in HEALTH_CHECK_VARS:
        assert var not in env


@pytest.mark.parametrize("var", HEALTH_CHECK_KUBESPRAY_VARS[1:])
def test_health_check_needs_address(var: str) -> None:
    """Tuning a knob without an address must not emit anything."""
    manifest_vars = default_vars()
    manifest_vars["kube_vip_bgp_enabled"] = True
    manifest_vars[var] = 5 if var.endswith(("_seconds", "_threshold")) else "/etc/ssl/certs/ca-bundle.crt"
    env = env_vars(render(manifest_vars))
    assert "control_plane_health_check_address" not in env
    assert var[len("kube_vip_"):] not in env


def test_health_check_enabled() -> None:
    """Setting the address enables the check and carries the tuning knobs."""
    manifest_vars = default_vars()
    manifest_vars["kube_vip_bgp_enabled"] = True
    manifest_vars["kube_vip_control_plane_health_check_address"] = "https://localhost:6443/livez"
    manifest_vars["kube_vip_control_plane_health_check_period_seconds"] = 10
    manifest_vars["kube_vip_control_plane_health_check_timeout_seconds"] = 2
    manifest_vars["kube_vip_control_plane_health_check_failure_threshold"] = 5
    manifest_vars["kube_vip_control_plane_health_check_ca_path"] = "/etc/kubernetes/pki/ca.crt"

    env = env_vars(render(manifest_vars))
    assert env["control_plane_health_check_address"] == "https://localhost:6443/livez"
    assert env["control_plane_health_check_period_seconds"] == "10"
    assert env["control_plane_health_check_timeout_seconds"] == "2"
    assert env["control_plane_health_check_failure_threshold"] == "5"
    assert env["control_plane_health_check_ca_path"] == "/etc/kubernetes/pki/ca.crt"


def test_health_check_address_only() -> None:
    """The address alone yields exactly one env var; kube-vip defaults apply."""
    manifest_vars = default_vars()
    manifest_vars["kube_vip_bgp_enabled"] = True
    manifest_vars["kube_vip_control_plane_health_check_address"] = "http://127.0.0.1:6443/livez"
    env = env_vars(render(manifest_vars))
    assert env["control_plane_health_check_address"] == "http://127.0.0.1:6443/livez"
    for var in HEALTH_CHECK_VARS[1:]:
        assert var not in env


@pytest.mark.parametrize("bgp_enabled", [True, False])
def test_health_check_produces_valid_manifest(bgp_enabled: bool) -> None:
    """Enabling the health check must keep the manifest valid YAML."""
    manifest_vars = default_vars()
    manifest_vars["kube_vip_bgp_enabled"] = bgp_enabled
    manifest_vars["kube_vip_control_plane_health_check_address"] = "https://localhost:6443/livez"
    manifest_vars["kube_vip_control_plane_health_check_period_seconds"] = 5
    manifest_vars["kube_vip_control_plane_health_check_timeout_seconds"] = 3
    manifest_vars["kube_vip_control_plane_health_check_failure_threshold"] = 3
    manifest_vars["kube_vip_control_plane_health_check_ca_path"] = "/etc/kubernetes/pki/ca.crt"

    manifest = yaml.safe_load(render(manifest_vars))
    assert manifest["kind"] == "Pod"
    names = [e["name"] for e in manifest["spec"]["containers"][0]["env"]]
    assert names.count("control_plane_health_check_address") == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
