# profile_tasks.py: an Ansible plugin for timing tasks

# Copyright (C) 2014 Jharrod LaFon <jharrod.lafon@gmail.com>
# https://github.com/jlafon/ansible-profile/
# Included with permission


# The MIT License (MIT)
#
# Copyright (c) 2014 Jharrod LaFon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from ansible.plugins.callback import CallbackBase
import time


class CallbackModule(CallbackBase):
    """
    A plugin for timing tasks
    """
    def __init__(self):
        self.stats = {}
        self.current = None

    def playbook_on_task_start(self, name, is_conditional):
        """
        Logs the start of each task
        """
        if self.current is not None:
            # Record the running time of the last executed task
            self.stats[self.current] = time.time() - self.stats[self.current]

        # Record the start time of the current task
        self.current = name
        self.stats[self.current] = time.time()

    called = False

    def playbook_on_stats(self, stats):
        """
        Prints the timings
        """
        if CallbackModule.called:
            return
        CallbackModule.called = True

        # Record the timing of the very last task
        if self.current is not None:
            self.stats[self.current] = time.time() - self.stats[self.current]

        # Sort the tasks by their running time
        results = sorted(self.stats.items(),
                         key=lambda value: value[1], reverse=True)

        # Just keep the top 10
        results = results[:10]

        # Print the timings
        for name, elapsed in results:
            print("{0:-<70}{1:->9}".format(
                    '{0} '.format(name),
                    ' {0:.02f}s'.format(elapsed)))

