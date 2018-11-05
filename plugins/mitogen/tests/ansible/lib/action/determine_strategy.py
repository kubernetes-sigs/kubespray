
import sys

from ansible.plugins.strategy import StrategyBase
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def _get_strategy_name(self):
        frame = sys._getframe()
        while frame:
            st = frame.f_locals.get('self')
            if isinstance(st, StrategyBase):
                return '%s.%s' % (type(st).__module__, type(st).__name__)
            frame = frame.f_back
        return ''

    def run(self, tmp=None, task_vars=None):
        return {
            'changed': False,
            'ansible_facts': {
                'strategy': self._get_strategy_name(),
                'is_mitogen': 'ansible_mitogen' in self._get_strategy_name(),
            }
        }
