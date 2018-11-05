"""
Fetch the connection configuration stack that would be used to connect to a
target, without actually connecting to it.
"""

import ansible_mitogen.connection

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if not isinstance(self._connection,
                          ansible_mitogen.connection.Connection):
            return {
                'skipped': True,
            }

        return {
            'changed': True,
            'result': self._connection._build_stack(),
        }
