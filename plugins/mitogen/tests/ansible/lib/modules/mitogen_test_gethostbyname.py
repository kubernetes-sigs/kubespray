#!/usr/bin/python

# I am a module that indirectly depends on glibc cached /etc/resolv.conf state.

import socket
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(argument_spec={'name': {'type': 'str'}})
    try:
        module.exit_json(addr=socket.gethostbyname(module.params['name']))
    except socket.error as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
