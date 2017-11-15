#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: kube
short_description: Manage Kubernetes Cluster
description:
  - Create, replace, remove, and stop resources within a Kubernetes Cluster
version_added: "2.0"
options:
  name:
    required: false
    default: null
    description:
      - The name associated with resource
  filename:
    required: false
    default: null
    description:
      - The path and filename of the resource(s) definition file.
  kubectl:
    required: false
    default: null
    description:
      - The path to the kubectl bin
  namespace:
    required: false
    default: null
    description:
      - The namespace associated with the resource(s)
  resource:
    required: false
    default: null
    description:
      - The resource to perform an action on. pods (po), replicationControllers (rc), services (svc)
  label:
    required: false
    default: null
    description:
      - The labels used to filter specific resources.
  server:
    required: false
    default: null
    description:
      - The url for the API server that commands are executed against.
  force:
    required: false
    default: false
    description:
      - A flag to indicate to force delete, replace, or stop.
  all:
    required: false
    default: false
    description:
      - A flag to indicate delete all, stop all, or all namespaces when checking exists.
  log_level:
    required: false
    default: 0
    description:
      - Indicates the level of verbosity of logging by kubectl.
  state:
    required: false
    choices: ['present', 'absent', 'latest', 'reloaded', 'stopped']
    default: present
    description:
      - present handles checking existence or creating if definition file provided,
        absent handles deleting resource(s) based on other options,
        latest handles creating or updating based on existence,
        reloaded handles updating resource(s) definition using definition file,
        stopped handles stopping resource(s) based on other options.
requirements:
  - kubectl
author: "Kenny Jones (@kenjones-cisco)"
"""

EXAMPLES = """
- name: test nginx is present
  kube: name=nginx resource=rc state=present

- name: test nginx is stopped
  kube: name=nginx resource=rc state=stopped

- name: test nginx is absent
  kube: name=nginx resource=rc state=absent

- name: test nginx is present
  kube: filename=/tmp/nginx.yml
"""


class KubeManager(object):

    def __init__(self, module):

        self.module = module

        self.kubectl = module.params.get('kubectl')
        if self.kubectl is None:
            self.kubectl =  module.get_bin_path('kubectl', True)
        self.base_cmd = [self.kubectl]

        if module.params.get('server'):
            self.base_cmd.append('--server=' + module.params.get('server'))

        if module.params.get('log_level'):
            self.base_cmd.append('--v=' + str(module.params.get('log_level')))

        if module.params.get('namespace'):
            self.base_cmd.append('--namespace=' + module.params.get('namespace'))

        self.all = module.params.get('all')
        self.force = module.params.get('force')
        self.name = module.params.get('name')
        self.filename = module.params.get('filename')
        self.resource = module.params.get('resource')
        self.label = module.params.get('label')

    def _execute(self, cmd):
        args = self.base_cmd + cmd
        try:
            rc, out, err = self.module.run_command(args)
            if rc != 0:
                self.module.fail_json(
                    msg='error running kubectl (%s) command (rc=%d): %s' % (' '.join(args), rc, out or err))
        except Exception as exc:
            self.module.fail_json(
                msg='error running kubectl (%s) command: %s' % (' '.join(args), str(exc)))
        return out.splitlines()

    def _execute_nofail(self, cmd):
        args = self.base_cmd + cmd
        rc, out, err = self.module.run_command(args)
        if rc != 0:
            return None
        return out.splitlines()

    def create(self, check=True, force=True):
        if check and self.exists():
            return []

        cmd = ['apply']

        if force:
            cmd.append('--force')

        if not self.filename:
            self.module.fail_json(msg='filename required to create')

        cmd.append('--filename=' + self.filename)

        return self._execute(cmd)

    def replace(self, force=True):

        cmd = ['apply']

        if force:
            cmd.append('--force')

        if not self.filename:
            self.module.fail_json(msg='filename required to reload')

        cmd.append('--filename=' + self.filename)

        return self._execute(cmd)

    def delete(self):

        if not self.force and not self.exists():
            return []

        cmd = ['delete']

        if self.filename:
            cmd.append('--filename=' + self.filename)
        else:
            if not self.resource:
                self.module.fail_json(msg='resource required to delete without filename')

            cmd.append(self.resource)

            if self.name:
                cmd.append(self.name)

            if self.label:
                cmd.append('--selector=' + self.label)

            if self.all:
                cmd.append('--all')

            if self.force:
                cmd.append('--ignore-not-found')

        return self._execute(cmd)

    def exists(self):
        cmd = ['get']

        if not self.resource:
            return False

        cmd.append(self.resource)

        if self.name:
            cmd.append(self.name)

        cmd.append('--no-headers')

        if self.label:
            cmd.append('--selector=' + self.label)

        if self.all:
            cmd.append('--all-namespaces')

        result = self._execute_nofail(cmd)
        if not result:
            return False
        return True

    def stop(self):

        if not self.force and not self.exists():
            return []

        cmd = ['stop']

        if self.filename:
            cmd.append('--filename=' + self.filename)
        else:
            if not self.resource:
                self.module.fail_json(msg='resource required to stop without filename')

            cmd.append(self.resource)

            if self.name:
                cmd.append(self.name)

            if self.label:
                cmd.append('--selector=' + self.label)

            if self.all:
                cmd.append('--all')

            if self.force:
                cmd.append('--ignore-not-found')

        return self._execute(cmd)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(),
            filename=dict(),
            namespace=dict(),
            resource=dict(),
            label=dict(),
            server=dict(),
            kubectl=dict(),
            force=dict(default=False, type='bool'),
            all=dict(default=False, type='bool'),
            log_level=dict(default=0, type='int'),
            state=dict(default='present', choices=['present', 'absent', 'latest', 'reloaded', 'stopped']),
            )
        )

    changed = False

    manager = KubeManager(module)
    state = module.params.get('state')
    if state == 'present':
        result = manager.create(check=False)

    elif state == 'absent':
        result = manager.delete()

    elif state == 'reloaded':
        result = manager.replace()

    elif state == 'stopped':
        result = manager.stop()

    elif state == 'latest':
        result = manager.replace()

    else:
        module.fail_json(msg='Unrecognized state %s.' % state)

    module.exit_json(changed=changed,
                     msg='success: %s' % (' '.join(result))
                     )


from ansible.module_utils.basic import *  # noqa
if __name__ == '__main__':
    main()
