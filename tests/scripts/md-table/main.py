#!/usr/bin/env python
import argparse
import sys
import glob
from pathlib import Path
import yaml
from pydblite import Base
import re
import jinja2
import sys

from pprint import pprint


parser = argparse.ArgumentParser(description='Generate a Markdown table representing the CI test coverage')
parser.add_argument('--dir', default='tests/files/', help='folder with test yml files')


args = parser.parse_args()
p = Path(args.dir)

env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=sys.path[0]))

# Data represents CI coverage data matrix
class Data:
    def __init__(self):
        self.db = Base(':memory:')
        self.db.create('container_manager', 'network_plugin', 'operating_system')

    
    def set(self, container_manager, network_plugin, operating_system):
        self.db.insert(container_manager=container_manager, network_plugin=network_plugin, operating_system=operating_system)
        self.db.commit()
    def exists(self, container_manager, network_plugin, operating_system):
        return len((self.db("container_manager") == container_manager) & (self.db("network_plugin") == network_plugin) & (self.db("operating_system") == operating_system)) > 0

    def jinja(self):
        template = env.get_template('table.md.j2')
        container_engines = list(self.db.get_unique_ids('container_manager'))
        network_plugins = list(self.db.get_unique_ids("network_plugin"))
        operating_systems = list(self.db.get_unique_ids("operating_system"))

        container_engines.sort()
        container_engines.reverse() # reverse sort container_engines to get Docker first in the list
        network_plugins.sort()
        operating_systems.sort()

        return template.render(
            container_engines=container_engines,
            network_plugins=network_plugins,
            operating_systems=operating_systems,
            exists=self.exists
        )

    def markdown(self):
        out = ''
        for container_manager in self.db.get_unique_ids('container_manager'):
            # Prepare the headers
            out += "# " + container_manager + "\n"
            headers = '|OS / CNI| '
            underline = '|----|'
            for network_plugin in self.db.get_unique_ids("network_plugin"):
                headers += network_plugin + ' | '
                underline += '----|'
            out += headers + "\n" + underline + "\n"
            for operating_system in self.db.get_unique_ids("operating_system"):
                out += '| ' + operating_system + ' | '
                for network_plugin in self.db.get_unique_ids("network_plugin"):
                    if self.exists(container_manager, network_plugin, operating_system):
                        emoji = ':white_check_mark:'
                    else:
                        emoji = ':x:'
                    out += emoji + ' | '
                out += "\n"

        pprint(self.db.get_unique_ids('operating_system'))
        pprint(self.db.get_unique_ids('network_plugin'))
        return out



if not p.is_dir():
    print("Path is not a directory")
    sys.exit(2)

data = Data()
files = p.glob('*.yml')
for f in files:
    y = yaml.load(f.open(), Loader=yaml.FullLoader)

    container_manager = y.get('container_manager', 'docker')
    network_plugin = y.get('kube_network_plugin', 'calico')
    x = re.match(r"^[a-z-]+_([a-z0-9]+).*", f.name)
    operating_system = x.group(1)
    data.set(container_manager=container_manager, network_plugin=network_plugin, operating_system=operating_system)
#print(data.markdown())
print(data.jinja())