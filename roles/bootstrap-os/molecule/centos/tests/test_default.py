
#   Copyright 2020
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_ensures_fastestmirror_plugin_is_disabled(host):
    conf = host.file("/etc/yum/pluginconf.d/fastestmirror.conf")
    if conf.exists:
        assert conf.contains("^enabled=0")


def test_ensures_libselinux_is_installed(host):
    assert (host.package("libselinux-python").is_installed or
            host.package("python3-libselinux").is_installed)
