# I am an Ansible action plug-in. I run the script provided in the parameter in
# the context of the action.

import sys

from ansible.plugins.action import ActionBase


def execute(s, gbls, lcls):
    if sys.version_info > (3,):
        exec(s, gbls, lcls)
    else:
        exec('exec s in gbls, lcls')


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp=tmp, task_vars=task_vars)
        lcls = {
            'self': self,
            'result': {}
        }
        execute(self._task.args['script'], globals(), lcls)
        return lcls['result']


if __name__ == '__main__':
    main()
