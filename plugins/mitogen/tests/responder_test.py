
import mock
import textwrap
import subprocess
import sys

import unittest2

import mitogen.master
import testlib

import plain_old_module
import simple_pkg.a


class NeutralizeMainTest(testlib.RouterMixin, unittest2.TestCase):
    klass = mitogen.master.ModuleResponder

    def call(self, *args, **kwargs):
        return self.klass(self.router).neutralize_main(*args, **kwargs)

    def test_missing_exec_guard(self):
        path = testlib.data_path('main_with_no_exec_guard.py')
        args = [sys.executable, path]
        proc = subprocess.Popen(args, stderr=subprocess.PIPE)
        _, stderr = proc.communicate()
        self.assertEquals(1, proc.returncode)
        expect = self.klass.main_guard_msg % (path,)
        self.assertTrue(expect in stderr.decode())

    HAS_MITOGEN_MAIN = mitogen.core.b(
        textwrap.dedent("""
            herp derp

            def myprog():
                pass

            @mitogen.main(maybe_some_option=True)
            def main(router):
                pass
        """)
    )

    def test_mitogen_main(self):
        untouched = self.call("derp.py", self.HAS_MITOGEN_MAIN)
        self.assertEquals(untouched, self.HAS_MITOGEN_MAIN)

    HAS_EXEC_GUARD = mitogen.core.b(
        textwrap.dedent("""
            herp derp

            def myprog():
                pass

            def main():
                pass

            if __name__ == '__main__':
                main()
        """)
    )

    def test_exec_guard(self):
        touched = self.call("derp.py", self.HAS_EXEC_GUARD)
        bits = touched.decode().split()
        self.assertEquals(bits[-3:], ['def', 'main():', 'pass'])



class GoodModulesTest(testlib.RouterMixin, unittest2.TestCase):
    def test_plain_old_module(self):
        # The simplest case: a top-level module with no interesting imports or
        # package machinery damage.
        context = self.router.local()
        self.assertEquals(256, context.call(plain_old_module.pow, 2, 8))

    def test_simple_pkg(self):
        # Ensure success of a simple package containing two submodules, one of
        # which imports the other.
        context = self.router.local()
        self.assertEquals(3,
            context.call(simple_pkg.a.subtract_one_add_two, 2))

    def test_self_contained_program(self):
        # Ensure a program composed of a single script can be imported
        # successfully.
        args = [sys.executable, testlib.data_path('self_contained_program.py')]
        output = testlib.subprocess__check_output(args).decode()
        self.assertEquals(output, "['__main__', 50]\n")


class BrokenModulesTest(unittest2.TestCase):
    def test_obviously_missing(self):
        # Ensure we don't crash in the case of a module legitimately being
        # unavailable. Should never happen in the real world.

        stream = mock.Mock()
        stream.sent_modules = set()
        router = mock.Mock()
        router.stream_by_id = lambda n: stream

        msg = mitogen.core.Message(
            data=mitogen.core.b('non_existent_module'),
            reply_to=50,
        )
        msg.router = router

        responder = mitogen.master.ModuleResponder(router)
        responder._on_get_module(msg)
        self.assertEquals(1, len(router._async_route.mock_calls))

        call = router._async_route.mock_calls[0]
        msg, = call[1]
        self.assertEquals(mitogen.core.LOAD_MODULE, msg.handle)
        self.assertEquals(('non_existent_module', None, None, None, ()),
                          msg.unpickle())

    def test_ansible_six_messed_up_path(self):
        # The copy of six.py shipped with Ansible appears in a package whose
        # __path__ subsequently ends up empty, which prevents pkgutil from
        # finding its submodules. After ansible.compat.six is initialized in
        # the parent, attempts to execute six/__init__.py on the slave will
        # cause an attempt to request ansible.compat.six._six from the master.
        import six_brokenpkg

        stream = mock.Mock()
        stream.sent_modules = set()
        router = mock.Mock()
        router.stream_by_id = lambda n: stream

        msg = mitogen.core.Message(
            data=mitogen.core.b('six_brokenpkg._six'),
            reply_to=50,
        )
        msg.router = router

        responder = mitogen.master.ModuleResponder(router)
        responder._on_get_module(msg)
        self.assertEquals(1, len(router._async_route.mock_calls))

        call = router._async_route.mock_calls[0]
        msg, = call[1]
        self.assertEquals(mitogen.core.LOAD_MODULE, msg.handle)
        self.assertIsInstance(msg.unpickle(), tuple)


class BlacklistTest(unittest2.TestCase):
    @unittest2.skip('implement me')
    def test_whitelist_no_blacklist(self):
        assert 0

    @unittest2.skip('implement me')
    def test_whitelist_has_blacklist(self):
        assert 0

    @unittest2.skip('implement me')
    def test_blacklist_no_whitelist(self):
        assert 0

    @unittest2.skip('implement me')
    def test_blacklist_has_whitelist(self):
        assert 0


if __name__ == '__main__':
    unittest2.main()
