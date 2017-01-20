# Copyright 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock
import unittest

from collections import OrderedDict
import sys

path = "./contrib/inventory_builder/"
if path not in sys.path:
    sys.path.append(path)

import inventory


class TestInventory(unittest.TestCase):
    @mock.patch('inventory.sys')
    def setUp(self, sys_mock):
        sys_mock.exit = mock.Mock()
        super(TestInventory, self).setUp()
        self.data = ['10.90.3.2', '10.90.3.3', '10.90.3.4']
        self.inv = inventory.KargoInventory()

    def test_get_ip_from_opts(self):
        optstring = "ansible_host=10.90.3.2 ip=10.90.3.2"
        expected = "10.90.3.2"
        result = self.inv.get_ip_from_opts(optstring)
        self.assertEqual(expected, result)

    def test_get_ip_from_opts_invalid(self):
        optstring = "notanaddr=value something random!chars:D"
        self.assertRaisesRegexp(ValueError, "IP parameter not found",
                                self.inv.get_ip_from_opts, optstring)

    def test_ensure_required_groups(self):
        groups = ['group1', 'group2']
        self.inv.ensure_required_groups(groups)
        for group in groups:
            self.assertTrue(group in self.inv.config.sections())

    def test_get_host_id(self):
        hostnames = ['node99', 'no99de01', '01node01', 'node1.domain',
                     'node3.xyz123.aaa']
        expected = [99, 1, 1, 1, 3]
        for hostname, expected in zip(hostnames, expected):
            result = self.inv.get_host_id(hostname)
            self.assertEqual(expected, result)

    def test_get_host_id_invalid(self):
        bad_hostnames = ['node', 'no99de', '01node', 'node.111111']
        for hostname in bad_hostnames:
            self.assertRaisesRegexp(ValueError, "Host name must end in an",
                                    self.inv.get_host_id, hostname)

    def test_build_hostnames_add_one(self):
        changed_hosts = ['10.90.0.2']
        expected = OrderedDict([('node1',
                               'ansible_host=10.90.0.2 ip=10.90.0.2')])
        result = self.inv.build_hostnames(changed_hosts)
        self.assertEqual(expected, result)

    def test_build_hostnames_add_duplicate(self):
        changed_hosts = ['10.90.0.2']
        expected = OrderedDict([('node1',
                               'ansible_host=10.90.0.2 ip=10.90.0.2')])
        self.inv.config['all'] = expected
        result = self.inv.build_hostnames(changed_hosts)
        self.assertEqual(expected, result)

    def test_build_hostnames_add_two(self):
        changed_hosts = ['10.90.0.2', '10.90.0.3']
        expected = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        self.inv.config['all'] = OrderedDict()
        result = self.inv.build_hostnames(changed_hosts)
        self.assertEqual(expected, result)

    def test_build_hostnames_delete_first(self):
        changed_hosts = ['-10.90.0.2']
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        self.inv.config['all'] = existing_hosts
        expected = OrderedDict([
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        result = self.inv.build_hostnames(changed_hosts)
        self.assertEqual(expected, result)

    def test_exists_hostname_positive(self):
        hostname = 'node1'
        expected = True
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        result = self.inv.exists_hostname(existing_hosts, hostname)
        self.assertEqual(expected, result)

    def test_exists_hostname_negative(self):
        hostname = 'node99'
        expected = False
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        result = self.inv.exists_hostname(existing_hosts, hostname)
        self.assertEqual(expected, result)

    def test_exists_ip_positive(self):
        ip = '10.90.0.2'
        expected = True
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        result = self.inv.exists_ip(existing_hosts, ip)
        self.assertEqual(expected, result)

    def test_exists_ip_negative(self):
        ip = '10.90.0.200'
        expected = False
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        result = self.inv.exists_ip(existing_hosts, ip)
        self.assertEqual(expected, result)

    def test_delete_host_by_ip_positive(self):
        ip = '10.90.0.2'
        expected = OrderedDict([
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        self.inv.delete_host_by_ip(existing_hosts, ip)
        self.assertEqual(expected, existing_hosts)

    def test_delete_host_by_ip_negative(self):
        ip = '10.90.0.200'
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3')])
        self.assertRaisesRegexp(ValueError, "Unable to find host",
                                self.inv.delete_host_by_ip, existing_hosts, ip)

    def test_purge_invalid_hosts(self):
        proper_hostnames = ['node1', 'node2']
        bad_host = 'doesnotbelong2'
        existing_hosts = OrderedDict([
            ('node1', 'ansible_host=10.90.0.2 ip=10.90.0.2'),
            ('node2', 'ansible_host=10.90.0.3 ip=10.90.0.3'),
            ('doesnotbelong2', 'whateveropts=ilike')])
        self.inv.config['all'] = existing_hosts
        self.inv.purge_invalid_hosts(proper_hostnames)
        self.assertTrue(bad_host not in self.inv.config['all'].keys())

    def test_add_host_to_group(self):
        group = 'etcd'
        host = 'node1'
        opts = 'ip=10.90.0.2'

        self.inv.add_host_to_group(group, host, opts)
        self.assertEqual(self.inv.config[group].get(host), opts)

    def test_set_kube_master(self):
        group = 'kube-master'
        host = 'node1'

        self.inv.set_kube_master([host])
        self.assertTrue(host in self.inv.config[group])

    def test_set_all(self):
        group = 'all'
        hosts = OrderedDict([
            ('node1', 'opt1'),
            ('node2', 'opt2')])

        self.inv.set_all(hosts)
        for host, opt in hosts.items():
            self.assertEqual(self.inv.config[group].get(host), opt)

    def test_set_k8s_cluster(self):
        group = 'k8s-cluster:children'
        expected_hosts = ['kube-node', 'kube-master']

        self.inv.set_k8s_cluster()
        for host in expected_hosts:
            self.assertTrue(host in self.inv.config[group])

    def test_set_kube_node(self):
        group = 'kube-node'
        host = 'node1'

        self.inv.set_kube_node([host])
        self.assertTrue(host in self.inv.config[group])

    def test_set_etcd(self):
        group = 'etcd'
        host = 'node1'

        self.inv.set_etcd([host])
        self.assertTrue(host in self.inv.config[group])

    def test_scale_scenario_one(self):
        num_nodes = 50
        hosts = OrderedDict()

        for hostid in range(1, num_nodes+1):
            hosts["node" + str(hostid)] = ""

        self.inv.set_all(hosts)
        self.inv.set_etcd(hosts.keys()[0:3])
        self.inv.set_kube_master(hosts.keys()[0:2])
        self.inv.set_kube_node(hosts.keys())
        for h in range(3):
            self.assertFalse(hosts.keys()[h] in self.inv.config['kube-node'])

    def test_scale_scenario_two(self):
        num_nodes = 500
        hosts = OrderedDict()

        for hostid in range(1, num_nodes+1):
            hosts["node" + str(hostid)] = ""

        self.inv.set_all(hosts)
        self.inv.set_etcd(hosts.keys()[0:3])
        self.inv.set_kube_master(hosts.keys()[3:5])
        self.inv.set_kube_node(hosts.keys())
        for h in range(5):
            self.assertFalse(hosts.keys()[h] in self.inv.config['kube-node'])
