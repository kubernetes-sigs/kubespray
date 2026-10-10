#!/usr/bin/env python3
"""Run with python3 tests/scripts/test-feature-gates.py (requires ansible-core)."""

from pathlib import Path
import unittest

import yaml
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.loader import init_plugin_loader
from ansible.template import Templar, trust_as_template


ROOT = Path(__file__).resolve().parents[2]
KUBEADM = ROOT / "roles/kubernetes/control-plane/templates/kubeadm-config.v1beta4.yaml.j2"
KUBELET = ROOT / "roles/kubernetes/node/templates/kubelet-config.v1beta1.yaml.j2"


class FeatureGatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_plugin_loader()
        cls.loader = DataLoader()
        cls.defaults = {}
        for role in ("kubespray_defaults", "kubernetes/node", "kubernetes/control-plane", "kubernetes/kubeadm_common"):
            for path in sorted((ROOT / "roles" / role / "defaults").rglob("*.yml")):
                cls.defaults.update(cls.loader.load_from_file(str(path), trusted_as_template=True))
        cls.defaults.update(cls.loader.load_from_file(
            str(ROOT / "roles/kubespray_defaults/vars/main/main.yml"), trusted_as_template=True))
        cls.defaults.update({
            "kube_version": "1.36.0", "container_manager": "containerd",
            "main_ip": "127.0.0.1", "main_ips": ["127.0.0.1"],
            "hostvars": {"node1": {"main_ip": "127.0.0.1", "main_access_ip": "127.0.0.1"}},
            "groups": {"kube_control_plane": ["node1"], "kube_node": ["node1"], "etcd": ["node1"]},
            "inventory_hostname": "node1", "group_names": ["kube_control_plane", "kube_node"],
            "ansible_facts": {"os_family": "Debian", "architecture": "x86_64"},
            "kubeadm_config_api_fqdn": "api.example.com",
            "etcd_access_addresses": "https://127.0.0.1:2379", "apiserver_sans": ["127.0.0.1"],
            "calico_ipam_host_local": False,
        })
        cls.validation = cls.loader.load_from_file(
            str(ROOT / "roles/kubernetes/preinstall/tasks/0040-verify-settings.yml"),
            trusted_as_template=True)[0]

    def render(self, **variables):
        templar = Templar(loader=self.loader, variables=self.defaults | variables)
        documents = list(yaml.safe_load_all(templar.template(trust_as_template(KUBEADM.read_text()))))
        configs = {document["kind"]: document for document in documents}
        standalone = yaml.safe_load(templar.template(trust_as_template(KUBELET.read_text())))
        self.assertEqual(standalone.get("featureGates"), configs["KubeletConfiguration"].get("featureGates"))
        return configs

    def assert_component_gates(self, configs, expected):
        cluster = configs["ClusterConfiguration"]
        for component in ("apiServer", "controllerManager", "scheduler"):
            flags = [arg["value"] for arg in cluster[component]["extraArgs"] if arg["name"] == "feature-gates"]
            self.assertEqual(flags, [expected] if expected else [])

    def test_empty_defaults(self):
        configs = self.render()
        for kind in ("ClusterConfiguration", "KubeProxyConfiguration", "KubeletConfiguration"):
            self.assertNotIn("featureGates", configs[kind])
        self.assert_component_gates(configs, "")

    def test_global_inheritance_and_boolean_rendering(self):
        gates = {"EnabledGate": True, "DisabledGate": False}
        configs = self.render(kube_feature_gates=gates)
        self.assert_component_gates(configs, "EnabledGate=true,DisabledGate=false")
        for kind in ("KubeProxyConfiguration", "KubeletConfiguration"):
            self.assertEqual(configs[kind]["featureGates"], gates)
            self.assertTrue(all(type(value) is bool for value in configs[kind]["featureGates"].values()))
        self.assertNotIn("featureGates", configs["ClusterConfiguration"])

    def test_component_replacement_and_independent_kubeadm_gates(self):
        gates = {"ComponentGate": False}
        variables = {name: gates for name in self.validation["loop"] if name != "kube_feature_gates"}
        configs = self.render(kube_feature_gates={"GlobalGate": True}, **variables)
        self.assert_component_gates(configs, "ComponentGate=false")
        for kind in ("ClusterConfiguration", "KubeProxyConfiguration", "KubeletConfiguration"):
            self.assertEqual(configs[kind]["featureGates"], gates)
        configs = self.render(kubeadm_feature_gates=gates)
        self.assertEqual(configs["ClusterConfiguration"]["featureGates"], gates)
        self.assertNotIn("featureGates", configs["KubeletConfiguration"])
        self.assertNotIn("featureGates", configs["KubeProxyConfiguration"])
        self.assert_component_gates(configs, "")

    def test_docker_override(self):
        for version in ("1.35.9", "1.36.0", "1.37.0"):
            for runtime in ("docker", "containerd", "crio"):
                for source in ("kube_feature_gates", "kubelet_feature_gates"):
                    for gates in ({}, {"ExtendWebSocketsToKubelet": True, "OtherGate": False}):
                        with self.subTest(version=version, runtime=runtime, source=source, gates=gates):
                            expected = dict(gates)
                            if runtime == "docker" and version != "1.35.9":
                                expected["ExtendWebSocketsToKubelet"] = False
                            configs = self.render(kube_version=version, container_manager=runtime, **{source: gates})
                            self.assertEqual(configs["KubeletConfiguration"].get("featureGates", {}), expected)
                            self.assertEqual(gates.get("ExtendWebSocketsToKubelet"), True if gates else None)

    def test_preflight_rejects_legacy_lists(self):
        for name in self.validation["loop"]:
            for gates in ({}, {"NodeSwap": True}, [], ["NodeSwap=true"]):
                with self.subTest(variable=name, gates=gates):
                    templar = Templar(loader=self.loader, variables=self.defaults | {name: gates, "item": name})
                    self.assertEqual(templar.evaluate_conditional(self.validation["assert"]["that"]), isinstance(gates, dict))
                    message = templar.template(self.validation["assert"]["fail_msg"])
                    self.assertIn(name, message)
                    self.assertIn("{NodeSwap: true}", message)


if __name__ == "__main__":
    unittest.main()
