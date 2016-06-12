#!/usr/bin/python
# -*- coding: utf-8 -*-

import kpm.deploy
from ansible.module_utils.basic import *

DOCUMENTATION = """
---
module: kpm
short_description: Application deployment on kubernetes with kpm registry
description:
  - Create, remove, and update resources within a Kubernetes Cluster
version_added: "2.0"
options:
  name:
    required: true
    default: null
    description:
      - The name of the kpm package
  namespace:
    required: false
    default: 'default'
    description:
      - The namespace to deploy package. It will be created if doesn't exist
  force:
    required: false
    default: false
    description:
      - A flag to indicate to force delete, replace.
  registry:
    required: false
    default: 'https://api.kpm.sh'
    description:
      - The registry url to fetch packages
  version:
    required: false
    default: 'None'
    description:
      - The package version
  variables:
    required: false
    default: 'None'
    description:
      - Set package variables
  state:
    required: false
    choices: ['present', 'absent']
    default: present
    description:
      - present handles checking existence or creating resources,
        absent handles deleting resource(s).
requirements:
  - kubectl
  - kpm
author: "Antoine Legrand (ant31_2t@msn.com)"
"""

EXAMPLES = """
- name: check presence or install ghost
  kpm: name=ghost/ghost state=present

- name: check absence or remove rocketchat
  kpm: name=ant31/rocketchat state=absent
"""

RETURN = """
"""


def check_changed(result, state='present'):
        no_change = ["ok", 'protected', 'absent']
        for r in result:
                if r['status'] not in no_change:
                        return True
        return False


def main():
        module = AnsibleModule(
                supports_check_mode=True,
                argument_spec = dict(
                        version = dict(default=None, required=False),
                        state = dict(default='present', choices=['present', 'absent']),
                        name = dict(required=True),
                        force = dict(required=False, default=False, type='bool'),
                        variables = dict(required=False, default=None, type='dict'),
                        registry = dict(required=False, default="https://api.kpm.sh"),
                        namespace=dict(default='default', required=False)))

        params = {"version": module.params.get("version"),
                  "namespace": module.params.get('namespace'),
                  "variables": module.params.get('variables'),
                  "endpoint": module.params.get('registry'),
                  "dry": module.check_mode,
                  "proxy": None,
                  "fmt": "json"}
        state = module.params.get("state")
        try:
                if state == 'present':
                        r = kpm.deploy.deploy(module.params.get('name'), **params)
                elif state == 'absent':
                        r = kpm.deploy.delete(module.params.get('name'), **params)
        except Exception as e:
                module.fail_json(msg=e.message)
        res = {}
        res['kpm'] = r
        res['changed'] = check_changed(r, state)
        module.exit_json(**res)

if __name__ == '__main__':
        main()
