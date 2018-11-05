
import os
import sys

import unittest2

import mitogen
import mitogen.ssh
import mitogen.utils

import testlib
import plain_old_module


def get_sys_executable():
    return sys.executable


def get_os_environ():
    return dict(os.environ)


class LocalTest(testlib.RouterMixin, unittest2.TestCase):
    stream_class = mitogen.ssh.Stream

    def test_stream_name(self):
        context = self.router.local()
        pid = context.call(os.getpid)
        self.assertEquals('local.%d' % (pid,), context.name)


class PythonPathTest(testlib.RouterMixin, unittest2.TestCase):
    stream_class = mitogen.ssh.Stream

    def test_inherited(self):
        context = self.router.local()
        self.assertEquals(sys.executable, context.call(get_sys_executable))

    def test_string(self):
        os.environ['PYTHON'] = sys.executable
        context = self.router.local(
            python_path=testlib.data_path('env_wrapper.sh'),
        )
        self.assertEquals(sys.executable, context.call(get_sys_executable))
        env = context.call(get_os_environ)
        self.assertEquals('1', env['EXECUTED_VIA_ENV_WRAPPER'])

    def test_list(self):
        context = self.router.local(
            python_path=[
                testlib.data_path('env_wrapper.sh'),
                "magic_first_arg",
                sys.executable
            ]
        )
        self.assertEquals(sys.executable, context.call(get_sys_executable))
        env = context.call(get_os_environ)
        self.assertEquals('magic_first_arg', env['ENV_WRAPPER_FIRST_ARG'])
        self.assertEquals('1', env['EXECUTED_VIA_ENV_WRAPPER'])


if __name__ == '__main__':
    unittest2.main()
