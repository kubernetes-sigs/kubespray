#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.externalpkg import extmod

def main():
    module = AnsibleModule(argument_spec={})
    module.exit_json(extmod_path=extmod.path())

if __name__ == '__main__':
    main()
