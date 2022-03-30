#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: kube_info
short_description: Get info from kubernetes resources
description:
  - Retrieve information from a kubernetes resource
version_added: "1.0"
options:
  kubectl:
    required: false
    default: autodetect is attempted by the ansible module
    description:
      - The path to the kubectl bin
  name:
    required: false
    default: null
    description:
      - The name associated with resource
      - If no name is provided all the resources in the namespace will be returned 
  namespace:
    required: false
    default: default
    description:
      - The namespace associated with the resource(s)
  resource:
    required: true
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
  tofile:
    required: false
    default: null
    description:
        - Dumps the information into a file
  state:
    required: false
    choices: ['present', 'check']
    default: present
    description:
      - present handles checking  versus de resource state, it makes the task fail if the state does not match the provided one
      - The check state won't fail even if the resource does not exist.             


requirements:
  - kubectl
author: "Alvaro Campesino (@Alvaro-Campesino)"
"""

EXAMPLES = """
- name: Get nginx-cm configmap
  kube_info: 
    name=nginx-cm 
    resource=configmap
    namespace=nginx-k8s
  register: ngninx_info

- name: Fail if nginx-cm configmap does not exist
  kube_info: 
    name=nginx-cm 
    resource=configmap
    state=present

- name: Get all pods with a label component=kube-apiserver
  kube_info: 
    resource=pod
    namespace=kube-system
    label="component=kube-apiserver"      
"""


class KubeManager(object):

    def __init__(self, module):

        self.module = module

        self.kubectl = module.params.get('kubectl')
        if self.kubectl is None:
            self.kubectl = module.get_bin_path('kubectl', True)

        self.base_cmd = [self.kubectl, 'get', '-o', 'json', '--ignore-not-found']

        if module.params.get('server'):
            self.base_cmd.append('--server=' + module.params.get('server'))

        if module.params.get('namespace'):
            if module.params.get('namespace') == 'all':
                self.base_cmd.append('-A')
            else:
                self.base_cmd.append('--namespace=' + module.params.get('namespace'))

        if module.params.get('label'):
            self.base_cmd.append('-l \'{}\''.format(module.params.get('label')))

        self.resource = module.params.get('resource').lower()
        self.base_cmd.append(self.resource)

        if module.params.get('name'):
            self.base_cmd.append(module.params.get('name'))

        self.state = module.params.get('state')
        self.tofile = module.params.get('tofile')

    def _kubectl_failure(self, rc, out, err):
        """'Manage errors while running kubectl"""
        self.module.fail_json(
            msg = 'error running kubectl (%s) command (rc=%d), out=\'%s\', err=\'%s\'' % (
                ' '.join(self.base_cmd), rc, out, err))

    def execute(self):
        """Execute the kubectl command that will return the k8s_info"""
        # If resources is not 'all' check resource exists
        if self.resource != all:
            exists = self._check_resource_exists()
            if not exists:
                return "{}"
        try:
            rc, out, err = self.module.run_command(self.base_cmd)
            if rc != 0:
                self._kubectl_failure(rc, out, err)
            if self.tofile:
                try:
                    with open(self.tofile, "w") as f:
                        f.write(out)
                except Exception as exc:
                    self.module.fail_json(
                        msg = 'error writing information to file %s. %s' % (self.tofile, str(exc)))
        except Exception as exc:
            self.module.fail_json(
                msg = 'error running kubectl (%s) command: %s' % (' '.join(self.base_cmd), str(exc)))
        if not out:
            if self.state != "present":
                self.module.fail_json(
                    msg = 'There is no %s named %s in the specified namespace.' % (self.resource, self.name)
                )
            out = {}
        return out

    def _check_resource_exists(self):
        """Verify if the resource exists and warn or fail if it does not"""
        resources_cmd = [self.kubectl, 'api-resources', '-o', 'name']
        try:
            rc, out, err = self.module.run_command(resources_cmd)
            if rc != 0:
                self._kubectl_failure(rc, out, err)
        except Exception as exc:
            self.module.fail_json(
                msg = 'error running kubectl (%s) command: %s' % (' '.join(self.base_cmd), str(exc)))

        resources = out.splitlines()
        # kubectl api-resources returns all resources in plural we allow users to name them in singular
        resource = self.resource.split('.')
        if not resource[0].endswith('s'):
            resource[0] = resource[0] + 's'
        resource = '.'.join(resource)

        if resource not in resources and self.state != "check":
            self.module.fail_json(
                msg = 'Error, resource %s does not exist in the k8s cluster' % self.resource
            )
        elif resource not in resources:
            msg = 'Resource %s does not exist in the k8s cluster, but we are in check mode' % self.resource
            return False
        else:
            return True


def main():
    fields = {
        "kubectl": {"required": False, "type": "str"},
        "label": {"required": False, "type": "str"},
        "name": {"required": False, "type": "str"},
        "namespace": {"required": False, "type": "str"},
        "resource": {"required": True, "type": "str"},
        "server": {"required": False, "type": "str"},
        "state": {"required": False, "type": "str", "choices": ['present', 'check'], "default": "check"},
        "tofile": {"required": False, "type": str}
    }

    module = AnsibleModule(argument_spec = fields)

    changed = False

    manager = KubeManager(module)
    result = manager.execute()

    module.exit_json(changed = changed,
                     k8s_info = json.loads(result)
                     )


from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()