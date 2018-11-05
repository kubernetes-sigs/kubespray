from __future__ import unicode_literals
import os
import io

from ansible import constants as C
from ansible.module_utils import six

try:
    from ansible.plugins import callback_loader
except ImportError:
    from ansible.plugins.loader import callback_loader

try:
    pprint = __import__(os.environ['NICE_STDOUT_PPRINT'])
except KeyError:
    pprint = None


def printi(tio, obj, key=None, indent=0):
    def write(s, *args):
        if args:
            s %= args
        tio.write('  ' * indent)
        if key is not None:
            tio.write('%s: ' % (key,))
        tio.write(s)
        tio.write('\n')

    if isinstance(obj, (list, tuple)):
        write('[')
        for i, obj2 in enumerate(obj):
            printi(tio, obj2, key=i, indent=indent+1)
        key = None
        write(']')
    elif isinstance(obj, dict):
        write('{')
        for key2, obj2 in sorted(six.iteritems(obj)):
            if not (key2.startswith('_ansible_') or
                    key2.endswith('_lines')):
                printi(tio, obj2, key=key2, indent=indent+1)
        key = None
        write('}')
    elif isinstance(obj, six.text_type):
        for line in obj.splitlines():
            write('%s', line.rstrip('\r\n'))
    elif isinstance(obj, six.binary_type):
        obj = obj.decode('utf-8', 'replace')
        for line in obj.splitlines():
            write('%s', line.rstrip('\r\n'))
    else:
        write('%r', obj)


DefaultModule = callback_loader.get('default', class_only=True)

class CallbackModule(DefaultModule):
    def _dump_results(self, result, *args, **kwargs):
        try:
            tio = io.StringIO()
            if pprint:
                pprint.pprint(result, stream=tio)
            else:
                printi(tio, result)
            return tio.getvalue() #.encode('ascii', 'replace')
        except:
            import traceback
            traceback.print_exc()
            raise

    def v2_runner_on_failed(self, result, ignore_errors=False):
        delegated_vars = result._result.get('_ansible_delegated_vars')
        self._clean_results(result._result, result._task.action)

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            return

        if delegated_vars:
            msg = "[%s -> %s]: FAILED! => %s" % (
                result._host.get_name(),
                delegated_vars['ansible_host'],
                self._dump_results(result._result),
            )
        else:
            msg = "[%s]: FAILED! => %s" % (
                result._host.get_name(),
                self._dump_results(result._result),
            )

        s = "fatal: %s: %s" % (
            result._task.get_path() or '(dynamic task)',
            msg,
        )
        self._display.display(s, color=C.COLOR_ERROR)
