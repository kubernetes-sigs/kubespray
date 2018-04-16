#!/usr/bin/python3
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Usage: inventory.py ip1 [ip2 ...]
# Examples: inventory.py 10.10.1.3 10.10.1.4 10.10.1.5
#
# Advanced usage:
# Add another host after initial creation: inventory.py 10.10.1.5
# Delete a host: inventory.py -10.10.1.3
# Delete a host by id: inventory.py -node1
#
# Load a YAML or JSON file with inventory data: inventory.py load hosts.yaml
# YAML file should be in the following format:
#    group1:
#      host1:
#        ip: X.X.X.X
#        var: val
#    group2:
#      host2:
#        ip: X.X.X.X

from collections import OrderedDict
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os
import re
import sys

ROLES = ['all', 'kube-master', 'kube-node', 'etcd', 'k8s-cluster:children',
         'calico-rr', 'vault']
PROTECTED_NAMES = ROLES
AVAILABLE_COMMANDS = ['help', 'print_cfg', 'print_ips', 'load']
_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


def get_var_as_bool(name, default):
    value = os.environ.get(name, '')
    return _boolean_states.get(value.lower(), default)

# Configurable as shell vars start

CONFIG_FILE = os.environ.get("CONFIG_FILE", "./inventory/sample/hosts.ini")
# Reconfigures cluster distribution at scale
SCALE_THRESHOLD = int(os.environ.get("SCALE_THRESHOLD", 50))
MASSIVE_SCALE_THRESHOLD = int(os.environ.get("SCALE_THRESHOLD", 200))

DEBUG = get_var_as_bool("DEBUG", True)
HOST_PREFIX = os.environ.get("HOST_PREFIX", "node")

# Configurable as shell vars end


class KubesprayInventory(object):

    def __init__(self, changed_hosts=None, config_file=None):
        self.config = configparser.ConfigParser(allow_no_value=True,
                                                delimiters=('\t', ' '))
        self.config_file = config_file
        if self.config_file:
            self.config.read(self.config_file)

        if changed_hosts and changed_hosts[0] in AVAILABLE_COMMANDS:
            self.parse_command(changed_hosts[0], changed_hosts[1:])
            sys.exit(0)

        self.ensure_required_groups(ROLES)

        if changed_hosts:
            self.hosts = self.build_hostnames(changed_hosts)
            self.purge_invalid_hosts(self.hosts.keys(), PROTECTED_NAMES)
            self.set_all(self.hosts)
            self.set_k8s_cluster()
            self.set_etcd(list(self.hosts.keys())[:3])
            if len(self.hosts) >= SCALE_THRESHOLD:
                self.set_kube_master(list(self.hosts.keys())[3:5])
            else:
                self.set_kube_master(list(self.hosts.keys())[:2])
            self.set_kube_node(self.hosts.keys())
            if len(self.hosts) >= SCALE_THRESHOLD:
                self.set_calico_rr(list(self.hosts.keys())[:3])
        else:  # Show help if no options
            self.show_help()
            sys.exit(0)

        self.write_config(self.config_file)

    def write_config(self, config_file):
        if config_file:
            with open(config_file, 'w') as f:
                self.config.write(f)
        else:
            print("WARNING: Unable to save config. Make sure you set "
                  "CONFIG_FILE env var.")

    def debug(self, msg):
        if DEBUG:
            print("DEBUG: {0}".format(msg))

    def get_ip_from_opts(self, optstring):
        opts = optstring.split(' ')
        for opt in opts:
            if '=' not in opt:
                continue
            k, v = opt.split('=')
            if k == "ip":
                return v
        raise ValueError("IP parameter not found in options")

    def ensure_required_groups(self, groups):
        for group in groups:
            try:
                self.debug("Adding group {0}".format(group))
                self.config.add_section(group)
            except configparser.DuplicateSectionError:
                pass

    def get_host_id(self, host):
        '''Returns integer host ID (without padding) from a given hostname.'''
        try:
            short_hostname = host.split('.')[0]
            return int(re.findall("\d+$", short_hostname)[-1])
        except IndexError:
            raise ValueError("Host name must end in an integer")

    def build_hostnames(self, changed_hosts):
        existing_hosts = OrderedDict()
        highest_host_id = 0
        try:
            for host, opts in self.config.items('all'):
                existing_hosts[host] = opts
                host_id = self.get_host_id(host)
                if host_id > highest_host_id:
                    highest_host_id = host_id
        except configparser.NoSectionError:
            pass

        # FIXME(mattymo): Fix condition where delete then add reuses highest id
        next_host_id = highest_host_id + 1

        all_hosts = existing_hosts.copy()
        for host in changed_hosts:
            if host[0] == "-":
                realhost = host[1:]
                if self.exists_hostname(all_hosts, realhost):
                    self.debug("Marked {0} for deletion.".format(realhost))
                    all_hosts.pop(realhost)
                elif self.exists_ip(all_hosts, realhost):
                    self.debug("Marked {0} for deletion.".format(realhost))
                    self.delete_host_by_ip(all_hosts, realhost)
            elif host[0].isdigit():
                if self.exists_hostname(all_hosts, host):
                    self.debug("Skipping existing host {0}.".format(host))
                    continue
                elif self.exists_ip(all_hosts, host):
                    self.debug("Skipping existing host {0}.".format(host))
                    continue

                next_host = "{0}{1}".format(HOST_PREFIX, next_host_id)
                next_host_id += 1
                all_hosts[next_host] = "ansible_host={0} ip={1}".format(
                    host, host)
            elif host[0].isalpha():
                raise Exception("Adding hosts by hostname is not supported.")

        return all_hosts

    def exists_hostname(self, existing_hosts, hostname):
        return hostname in existing_hosts.keys()

    def exists_ip(self, existing_hosts, ip):
        for host_opts in existing_hosts.values():
            if ip == self.get_ip_from_opts(host_opts):
                return True
        return False

    def delete_host_by_ip(self, existing_hosts, ip):
        for hostname, host_opts in existing_hosts.items():
            if ip == self.get_ip_from_opts(host_opts):
                del existing_hosts[hostname]
                return
        raise ValueError("Unable to find host by IP: {0}".format(ip))

    def purge_invalid_hosts(self, hostnames, protected_names=[]):
        for role in self.config.sections():
            for host, _ in self.config.items(role):
                if host not in hostnames and host not in protected_names:
                    self.debug("Host {0} removed from role {1}".format(host,
                               role))
                    self.config.remove_option(role, host)

    def add_host_to_group(self, group, host, opts=""):
        self.debug("adding host {0} to group {1}".format(host, group))
        self.config.set(group, host, opts)

    def set_kube_master(self, hosts):
        for host in hosts:
            self.add_host_to_group('kube-master', host)

    def set_all(self, hosts):
        for host, opts in hosts.items():
            self.add_host_to_group('all', host, opts)

    def set_k8s_cluster(self):
        self.add_host_to_group('k8s-cluster:children', 'kube-node')
        self.add_host_to_group('k8s-cluster:children', 'kube-master')

    def set_calico_rr(self, hosts):
        for host in hosts:
            if host in self.config.items('kube-master'):
                    self.debug("Not adding {0} to calico-rr group because it "
                               "conflicts with kube-master group".format(host))
                    continue
            if host in self.config.items('kube-node'):
                    self.debug("Not adding {0} to calico-rr group because it "
                               "conflicts with kube-node group".format(host))
                    continue
            self.add_host_to_group('calico-rr', host)

    def set_kube_node(self, hosts):
        for host in hosts:
            if len(self.config['all']) >= SCALE_THRESHOLD:
                if self.config.has_option('etcd', host):
                    self.debug("Not adding {0} to kube-node group because of "
                               "scale deployment and host is in etcd "
                               "group.".format(host))
                    continue
            if len(self.config['all']) >= MASSIVE_SCALE_THRESHOLD:
                if self.config.has_option('kube-master', host):
                    self.debug("Not adding {0} to kube-node group because of "
                               "scale deployment and host is in kube-master "
                               "group.".format(host))
                    continue
            self.add_host_to_group('kube-node', host)

    def set_etcd(self, hosts):
        for host in hosts:
            self.add_host_to_group('etcd', host)
            self.add_host_to_group('vault', host)

    def load_file(self, files=None):
        '''Directly loads JSON, or YAML file to inventory.'''

        if not files:
            raise Exception("No input file specified.")

        import json
        import yaml

        for filename in list(files):
            # Try JSON, then YAML
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
            except ValueError:
                try:
                    with open(filename, 'r') as f:
                        data = yaml.load(f)
                        print("yaml")
                except ValueError:
                    raise Exception("Cannot read %s as JSON, YAML, or CSV",
                                    filename)

            self.ensure_required_groups(ROLES)
            self.set_k8s_cluster()
            for group, hosts in data.items():
                self.ensure_required_groups([group])
                for host, opts in hosts.items():
                    optstring = "ansible_host={0} ip={0}".format(opts['ip'])
                    for key, val in opts.items():
                        if key == "ip":
                            continue
                        optstring += " {0}={1}".format(key, val)

                    self.add_host_to_group('all', host, optstring)
                    self.add_host_to_group(group, host)
            self.write_config(self.config_file)

    def parse_command(self, command, args=None):
        if command == 'help':
            self.show_help()
        elif command == 'print_cfg':
            self.print_config()
        elif command == 'print_ips':
            self.print_ips()
        elif command == 'load':
            self.load_file(args)
        else:
            raise Exception("Invalid command specified.")

    def show_help(self):
        help_text = '''Usage: inventory.py ip1 [ip2 ...]
Examples: inventory.py 10.10.1.3 10.10.1.4 10.10.1.5

Available commands:
help - Display this message
print_cfg - Write inventory file to stdout
print_ips - Write a space-delimited list of IPs from "all" group

Advanced usage:
Add another host after initial creation: inventory.py 10.10.1.5
Delete a host: inventory.py -10.10.1.3
Delete a host by id: inventory.py -node1

Configurable env vars:
DEBUG                   Enable debug printing. Default: True
CONFIG_FILE             File to write config to Default: ./inventory/sample/hosts.ini
HOST_PREFIX             Host prefix for generated hosts. Default: node
SCALE_THRESHOLD         Separate ETCD role if # of nodes >= 50
MASSIVE_SCALE_THRESHOLD Separate K8s master and ETCD if # of nodes >= 200
'''
        print(help_text)

    def print_config(self):
        self.config.write(sys.stdout)

    def print_ips(self):
        ips = []
        for host, opts in self.config.items('all'):
            ips.append(self.get_ip_from_opts(opts))
        print(' '.join(ips))


def main(argv=None):
    if not argv:
        argv = sys.argv[1:]
    KubesprayInventory(argv, CONFIG_FILE)

if __name__ == "__main__":
    sys.exit(main())
