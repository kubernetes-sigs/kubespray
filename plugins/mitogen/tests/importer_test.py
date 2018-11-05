
import email.utils
import sys
import threading
import types
import zlib

import mock
import pytest
import unittest2

import mitogen.core
import mitogen.utils
from mitogen.core import b

import testlib


class ImporterMixin(testlib.RouterMixin):
    modname = None

    def setUp(self):
        super(ImporterMixin, self).setUp()
        self.context = mock.Mock()
        self.importer = mitogen.core.Importer(self.router, self.context, '')

        # TODO: this is a horrendous hack. Without it, we can't deliver a
        # response to find_module() via _on_load_module() since find_module()
        # is still holding the lock. The tests need a nicer abstraction for
        # soemthing like "fake participant" that lets us have a mock master
        # that respects the execution model expected by the code -- probably
        # (grmph) including multiplexer thread and all.
        self.importer._lock = threading.RLock()

    def set_get_module_response(self, resp):
        def on_context_send(msg):
            self.context_send_msg = msg
            self.importer._on_load_module(
                mitogen.core.Message.pickled(resp)
            )
        self.context.send = on_context_send

    def tearDown(self):
        sys.modules.pop(self.modname, None)
        super(ImporterMixin, self).tearDown()


class LoadModuleTest(ImporterMixin, testlib.TestCase):
    data = zlib.compress(b("data = 1\n\n"))
    path = 'fake_module.py'
    modname = 'fake_module'

    # 0:fullname 1:pkg_present 2:path 3:compressed 4:related
    response = (modname, None, path, data, [])

    def test_no_such_module(self):
        self.set_get_module_response(
            # 0:fullname 1:pkg_present 2:path 3:compressed 4:related
            (self.modname, None, None, None, None)
        )
        self.assertRaises(ImportError,
            lambda: self.importer.load_module(self.modname))

    def test_module_added_to_sys_modules(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertIs(sys.modules[self.modname], mod)
        self.assertIsInstance(mod, types.ModuleType)

    def test_module_file_set(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertEquals(mod.__file__, 'master:' + self.path)

    def test_module_loader_set(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertIs(mod.__loader__, self.importer)

    def test_module_package_unset(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertIsNone(mod.__package__)


class LoadSubmoduleTest(ImporterMixin, testlib.TestCase):
    data = zlib.compress(b("data = 1\n\n"))
    path = 'fake_module.py'
    modname = 'mypkg.fake_module'
    # 0:fullname 1:pkg_present 2:path 3:compressed 4:related
    response = (modname, None, path, data, [])

    def test_module_package_unset(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertEquals(mod.__package__, 'mypkg')


class LoadModulePackageTest(ImporterMixin, testlib.TestCase):
    data = zlib.compress(b("func = lambda: 1\n\n"))
    path = 'fake_pkg/__init__.py'
    modname = 'fake_pkg'
    # 0:fullname 1:pkg_present 2:path 3:compressed 4:related
    response = (modname, [], path, data, [])

    def test_module_file_set(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertEquals(mod.__file__, 'master:' + self.path)

    def test_get_filename(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        filename = mod.__loader__.get_filename(self.modname)
        self.assertEquals('master:fake_pkg/__init__.py', filename)

    def test_get_source(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        source = mod.__loader__.get_source(self.modname)
        self.assertEquals(source,
            mitogen.core.to_text(zlib.decompress(self.data)))

    def test_module_loader_set(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertIs(mod.__loader__, self.importer)

    def test_module_path_present(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertEquals(mod.__path__, [])

    def test_module_package_set(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertEquals(mod.__package__, self.modname)

    def test_module_data(self):
        self.set_get_module_response(self.response)
        mod = self.importer.load_module(self.modname)
        self.assertIsInstance(mod.func, types.FunctionType)
        self.assertEquals(mod.func.__module__, self.modname)


class EmailParseAddrSysTest(testlib.RouterMixin, testlib.TestCase):
    @pytest.fixture(autouse=True)
    def initdir(self, caplog):
        self.caplog = caplog

    def test_sys_module_not_fetched(self):
        # An old version of core.Importer would request the email.sys module
        # while executing email.utils.parseaddr(). Ensure this needless
        # roundtrip has not reappeared.
        pass


class ImporterBlacklistTest(testlib.TestCase):
    def test_is_blacklisted_import_default(self):
        importer = mitogen.core.Importer(
            router=mock.Mock(), context=None, core_src='',
        )
        self.assertIsInstance(importer.whitelist, list)
        self.assertIsInstance(importer.blacklist, list)
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'mypkg'))
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'mypkg.mod'))
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'otherpkg'))
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'otherpkg.mod'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, '__builtin__'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'builtins'))

    def test_is_blacklisted_import_just_whitelist(self):
        importer = mitogen.core.Importer(
            router=mock.Mock(), context=None, core_src='',
            whitelist=('mypkg',),
        )
        self.assertIsInstance(importer.whitelist, list)
        self.assertIsInstance(importer.blacklist, list)
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'mypkg'))
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'mypkg.mod'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'otherpkg'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'otherpkg.mod'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, '__builtin__'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'builtins'))

    def test_is_blacklisted_import_just_blacklist(self):
        importer = mitogen.core.Importer(
            router=mock.Mock(), context=None, core_src='',
            blacklist=('mypkg',),
        )
        self.assertIsInstance(importer.whitelist, list)
        self.assertIsInstance(importer.blacklist, list)
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'mypkg'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'mypkg.mod'))
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'otherpkg'))
        self.assertFalse(mitogen.core.is_blacklisted_import(importer, 'otherpkg.mod'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, '__builtin__'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'builtins'))

    def test_is_blacklisted_import_whitelist_and_blacklist(self):
        importer = mitogen.core.Importer(
            router=mock.Mock(), context=None, core_src='',
            whitelist=('mypkg',), blacklist=('mypkg',),
        )
        self.assertIsInstance(importer.whitelist, list)
        self.assertIsInstance(importer.blacklist, list)
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'mypkg'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'mypkg.mod'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'otherpkg'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'otherpkg.mod'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, '__builtin__'))
        self.assertTrue(mitogen.core.is_blacklisted_import(importer, 'builtins'))


if __name__ == '__main__':
    unittest2.main()
