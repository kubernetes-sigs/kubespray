#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import external3

def main():
    module = AnsibleModule(argument_spec={})
    module.exit_json(external2_path=external3.path2(),
                     external3_path=external3.path())

if __name__ == '__main__':
    main()
