#!/usr/bin/python
# I expect the quote from modules2/module_utils/joker.py.

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import external1

def main():
    module = AnsibleModule(argument_spec={})
    module.exit_json(external1_path=external1.path(),
                     external2_path=external1.path2())

if __name__ == '__main__':
    main()
