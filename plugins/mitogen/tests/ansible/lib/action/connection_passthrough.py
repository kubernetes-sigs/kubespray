
import traceback
import sys

from ansible.plugins.strategy import StrategyBase
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        try:
            method = getattr(self._connection, self._task.args['method'])
            args = tuple(self._task.args.get('args', ()))
            kwargs = self._task.args.get('kwargs', {})

            return {
                'changed': False,
                'failed': False,
                'result': method(*args, **kwargs)
            }
        except Exception as e:
            traceback.print_exc()
            return {
                'changed': False,
                'failed': True,
                'msg': str(e),
                'result': e,
            }
