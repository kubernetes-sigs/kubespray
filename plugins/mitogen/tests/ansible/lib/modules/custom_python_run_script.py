#!/usr/bin/python
# I am an Ansible new-style Python module. I run the script provided in the
# parameter.

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_module_path
from ansible.module_utils import six

import os
import pwd
import socket
import sys


def execute(s, gbls, lcls):
    if sys.version_info > (3,):
        exec(s, gbls, lcls)
    else:
        exec('exec s in gbls, lcls')


def main():
    module = AnsibleModule(argument_spec={
        'script': {
            'type': str
        }
    })

    lcls = {
        'module': module,
        'result': {}
    }
    execute(module.params['script'], globals(), lcls)
    del lcls['module']
    module.exit_json(**lcls['result'])


if __name__ == '__main__':
    main()
