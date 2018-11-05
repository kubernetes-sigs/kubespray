#!/usr/bin/python
# I am an Ansible new-style Python module. I modify the process environment and
# don't clean up after myself.

from ansible.module_utils.basic import AnsibleModule

import os
import pwd
import socket
import sys


def main():
    module = AnsibleModule(argument_spec={
        'key': {'type': str},
        'val': {'type': str}
    })
    os.environ[module.params['key']] = module.params['val']
    module.exit_json(msg='Muahahaha!')

if __name__ == '__main__':
    main()
