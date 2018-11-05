"""
Arrange for all ContextService connections to be torn down unconditionally,
required for reliable LRU tests.
"""

import ansible_mitogen.connection
import ansible_mitogen.services
import mitogen.service

from ansible.plugins.strategy import StrategyBase
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if not isinstance(self._connection,
                          ansible_mitogen.connection.Connection):
            return {
                'skipped': True,
            }

        self._connection._connect()
        return {
            'changed': True,
            'result': self._connection.parent.call_service(
                service_name='ansible_mitogen.services.ContextService',
                method_name='shutdown_all',
            )
        }
