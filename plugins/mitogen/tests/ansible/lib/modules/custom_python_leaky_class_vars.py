#!/usr/bin/python
# I am an Ansible new-style Python module. I leak state from each invocation
# into a class variable and a global variable.

from ansible.module_utils.basic import AnsibleModule


leak1 = []


class MyClass:
    leak2 = []


def main():
    module = AnsibleModule(argument_spec={'name': {'type': 'str'}})
    leak1.append(module.params['name'])
    MyClass.leak2.append(module.params['name'])
    module.exit_json(
        leak1=leak1,
        leak2=MyClass.leak2,
    )

if __name__ == '__main__':
    main()
