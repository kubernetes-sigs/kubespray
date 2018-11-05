import inspect
import os
import sys

import unittest2

import mitogen.master

import testlib


class ConstructorTest(testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def test_simple(self):
        self.klass()


class ReprTest(testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def test_simple(self):
        self.assertEquals('ModuleFinder()', repr(self.klass()))


class IsStdlibNameTest(testlib.TestCase):
    func = staticmethod(mitogen.master.is_stdlib_name)

    def test_builtin(self):
        import sys
        self.assertTrue(self.func('sys'))

    def test_stdlib_1(self):
        import logging
        self.assertTrue(self.func('logging'))

    def test_stdlib_2(self):
        # virtualenv only symlinks some paths to its local site-packages
        # directory. Ensure both halves of the search path return the correct
        # result.
        import email
        self.assertTrue(self.func('email'))

    def test_mitogen_core(self):
        import mitogen.core
        self.assertFalse(self.func('mitogen.core'))

    def test_mitogen_fakessh(self):
        import mitogen.fakessh
        self.assertFalse(self.func('mitogen.fakessh'))


class GetModuleViaPkgutilTest(testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def call(self, fullname):
        return self.klass()._get_module_via_pkgutil(fullname)

    def test_empty_source_pkg(self):
        path, src, is_pkg = self.call('module_finder_testmod')
        self.assertEquals(path,
            testlib.data_path('module_finder_testmod/__init__.py'))
        self.assertEquals(mitogen.core.b(''), src)
        self.assertTrue(is_pkg)

    def test_empty_source_module(self):
        path, src, is_pkg = self.call('module_finder_testmod.empty_mod')
        self.assertEquals(path,
            testlib.data_path('module_finder_testmod/empty_mod.py'))
        self.assertEquals(mitogen.core.b(''), src)
        self.assertFalse(is_pkg)

    def test_regular_mod(self):
        from module_finder_testmod import regular_mod
        path, src, is_pkg = self.call('module_finder_testmod.regular_mod')
        self.assertEquals(path,
            testlib.data_path('module_finder_testmod/regular_mod.py'))
        self.assertEquals(mitogen.core.to_text(src),
                          inspect.getsource(regular_mod))
        self.assertFalse(is_pkg)


class GetModuleViaSysModulesTest(testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def call(self, fullname):
        return self.klass()._get_module_via_sys_modules(fullname)

    def test_main(self):
        import __main__
        path, src, is_pkg = self.call('__main__')
        self.assertEquals(path, __main__.__file__)
        self.assertEquals(src, open(path, 'rb').read())
        self.assertFalse(is_pkg)

    def test_dylib_fails(self):
        # _socket comes from a .so
        import _socket
        tup = self.call('_socket')
        self.assertIsNone(tup)

    def test_builtin_fails(self):
        # sys is built-in
        tup = self.call('sys')
        self.assertIsNone(tup)


class ResolveRelPathTest(testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def call(self, fullname, level):
        return self.klass().resolve_relpath(fullname, level)

    def test_empty(self):
        self.assertEquals('', self.call('', 0))
        self.assertEquals('', self.call('', 1))
        self.assertEquals('', self.call('', 2))

    def test_absolute(self):
        self.assertEquals('', self.call('email.utils', 0))

    def test_rel1(self):
        self.assertEquals('email.', self.call('email.utils', 1))

    def test_rel2(self):
        self.assertEquals('', self.call('email.utils', 2))

    def test_rel_overflow(self):
        self.assertEquals('', self.call('email.utils', 3))


class DjangoMixin(object):
    WEBPROJECT_PATH = testlib.data_path('webproject')

    # TODO: rip out Django and replace with a static tree of weird imports that
    # don't depend on .. Django! The hack below is because the version of
    # Django we need to test against 2.6 doesn't actually run on 3.6. But we
    # don't care, we just need to be able to import it.
    #
    #   File "django/utils/html_parser.py", line 12, in <module>
    # AttributeError: module 'html.parser' has no attribute 'HTMLParseError'
    #
    import pkg_resources._vendor.six
    from django.utils.six.moves import html_parser as _html_parser
    _html_parser.HTMLParseError = Exception

    @classmethod
    def setUpClass(cls):
        super(DjangoMixin, cls).setUpClass()
        sys.path.append(cls.WEBPROJECT_PATH)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'webproject.settings'

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(cls.WEBPROJECT_PATH)
        del os.environ['DJANGO_SETTINGS_MODULE']
        super(DjangoMixin, cls).tearDownClass()


class FindRelatedImportsTest(DjangoMixin, testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def call(self, fullname):
        return self.klass().find_related_imports(fullname)

    def test_simple(self):
        import mitogen.fakessh
        related = self.call('mitogen.fakessh')
        self.assertEquals(related, [
            'mitogen',
            'mitogen.core',
            'mitogen.master',
            'mitogen.parent',
        ])

    def test_django_db(self):
        import django.db
        related = self.call('django.db')
        self.assertEquals(related, [
            'django',
            'django.core',
            'django.core.signals',
            'django.db.utils',
            'django.utils.functional',
        ])

    def test_django_db_models(self):
        import django.db.models
        related = self.call('django.db.models')
        self.maxDiff=None
        self.assertEquals(related, [
            'django',
            'django.core.exceptions',
            'django.db',
            'django.db.models',
            'django.db.models.aggregates',
            'django.db.models.base',
            'django.db.models.deletion',
            'django.db.models.expressions',
            'django.db.models.fields',
            'django.db.models.fields.files',
            'django.db.models.fields.related',
            'django.db.models.fields.subclassing',
            'django.db.models.loading',
            'django.db.models.manager',
            'django.db.models.query',
            'django.db.models.signals',
        ])


class FindRelatedTest(DjangoMixin, testlib.TestCase):
    klass = mitogen.master.ModuleFinder

    def call(self, fullname):
        return self.klass().find_related(fullname)

    SIMPLE_EXPECT = set([
        'mitogen',
        'mitogen.core',
        'mitogen.master',
        'mitogen.minify',
        'mitogen.parent',
    ])

    if sys.version_info < (3, 2):
        SIMPLE_EXPECT.add('mitogen.compat')
        SIMPLE_EXPECT.add('mitogen.compat.functools')
    if sys.version_info < (2, 7):
        SIMPLE_EXPECT.add('mitogen.compat.tokenize')

    def test_simple(self):
        import mitogen.fakessh
        related = self.call('mitogen.fakessh')
        self.assertEquals(set(related), self.SIMPLE_EXPECT)


class DjangoFindRelatedTest(DjangoMixin, testlib.TestCase):
    klass = mitogen.master.ModuleFinder
    maxDiff = None

    def call(self, fullname):
        return self.klass().find_related(fullname)

    def test_django_db(self):
        import django.db
        related = self.call('django.db')
        self.assertEquals(related, [
            'django',
            'django.conf',
            'django.conf.global_settings',
            'django.core',
            'django.core.exceptions',
            'django.core.signals',
            'django.db.utils',
            'django.dispatch',
            'django.dispatch.dispatcher',
            'django.dispatch.saferef',
            'django.utils',
            'django.utils._os',
            'django.utils.encoding',
            'django.utils.functional',
            'django.utils.importlib',
            'django.utils.module_loading',
            'django.utils.six',
        ])

    def test_django_db_models(self):
        if sys.version_info >= (3, 0):
            raise unittest2.SkipTest('broken due to ancient vendored six.py')

        import django.db.models
        related = self.call('django.db.models')
        self.assertEquals(related, [
            'django',
            'django.conf',
            'django.conf.global_settings',
            'django.core',
            'django.core.exceptions',
            'django.core.files',
            'django.core.files.base',
            'django.core.files.images',
            'django.core.files.locks',
            'django.core.files.move',
            'django.core.files.storage',
            'django.core.files.utils',
            'django.core.signals',
            'django.core.validators',
            'django.db',
            'django.db.backends',
            'django.db.backends.signals',
            'django.db.backends.util',
            'django.db.models.aggregates',
            'django.db.models.base',
            'django.db.models.constants',
            'django.db.models.deletion',
            'django.db.models.expressions',
            'django.db.models.fields',
            'django.db.models.fields.files',
            'django.db.models.fields.proxy',
            'django.db.models.fields.related',
            'django.db.models.fields.subclassing',
            'django.db.models.loading',
            'django.db.models.manager',
            'django.db.models.options',
            'django.db.models.query',
            'django.db.models.query_utils',
            'django.db.models.related',
            'django.db.models.signals',
            'django.db.models.sql',
            'django.db.models.sql.aggregates',
            'django.db.models.sql.constants',
            'django.db.models.sql.datastructures',
            'django.db.models.sql.expressions',
            'django.db.models.sql.query',
            'django.db.models.sql.subqueries',
            'django.db.models.sql.where',
            'django.db.transaction',
            'django.db.utils',
            'django.dispatch',
            'django.dispatch.dispatcher',
            'django.dispatch.saferef',
            'django.forms',
            'django.forms.fields',
            'django.forms.forms',
            'django.forms.formsets',
            'django.forms.models',
            'django.forms.util',
            'django.forms.widgets',
            'django.utils',
            'django.utils._os',
            'django.utils.crypto',
            'django.utils.datastructures',
            'django.utils.dateformat',
            'django.utils.dateparse',
            'django.utils.dates',
            'django.utils.datetime_safe',
            'django.utils.decorators',
            'django.utils.deprecation',
            'django.utils.encoding',
            'django.utils.formats',
            'django.utils.functional',
            'django.utils.html',
            'django.utils.html_parser',
            'django.utils.importlib',
            'django.utils.ipv6',
            'django.utils.itercompat',
            'django.utils.module_loading',
            'django.utils.numberformat',
            'django.utils.safestring',
            'django.utils.six',
            'django.utils.text',
            'django.utils.timezone',
            'django.utils.translation',
            'django.utils.tree',
            'django.utils.tzinfo',
            'pytz',
            'pytz.exceptions',
            'pytz.lazy',
            'pytz.tzfile',
            'pytz.tzinfo',
        ])

if __name__ == '__main__':
    unittest2.main()
