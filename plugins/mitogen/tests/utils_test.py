#!/usr/bin/env python

import unittest2

import mitogen.core
import mitogen.master
import mitogen.utils


def func0(router):
    return router


@mitogen.utils.with_router
def func(router):
    return router


class RunWithRouterTest(unittest2.TestCase):
    # test_shutdown_on_exception
    # test_shutdown_on_success

    def test_run_with_broker(self):
        router = mitogen.utils.run_with_router(func0)
        self.assertIsInstance(router, mitogen.master.Router)
        self.assertFalse(router.broker._thread.isAlive())


class WithRouterTest(unittest2.TestCase):
    def test_with_broker(self):
        router = func()
        self.assertIsInstance(router, mitogen.master.Router)
        self.assertFalse(router.broker._thread.isAlive())


class Dict(dict): pass
class List(list): pass
class Tuple(tuple): pass
class Unicode(mitogen.core.UnicodeType): pass
class Bytes(mitogen.core.BytesType): pass


class CastTest(unittest2.TestCase):
    def test_dict(self):
        self.assertEqual(type(mitogen.utils.cast({})), dict)
        self.assertEqual(type(mitogen.utils.cast(Dict())), dict)

    def test_nested_dict(self):
        specimen = mitogen.utils.cast(Dict({'k': Dict({'k2': 'v2'})}))
        self.assertEqual(type(specimen), dict)
        self.assertEqual(type(specimen['k']), dict)

    def test_list(self):
        self.assertEqual(type(mitogen.utils.cast([])), list)
        self.assertEqual(type(mitogen.utils.cast(List())), list)

    def test_nested_list(self):
        specimen = mitogen.utils.cast(List((0, 1, List((None,)))))
        self.assertEqual(type(specimen), list)
        self.assertEqual(type(specimen[2]), list)

    def test_tuple(self):
        self.assertEqual(type(mitogen.utils.cast(())), list)
        self.assertEqual(type(mitogen.utils.cast(Tuple())), list)

    def test_nested_tuple(self):
        specimen = mitogen.utils.cast(Tuple((0, 1, Tuple((None,)))))
        self.assertEqual(type(specimen), list)
        self.assertEqual(type(specimen[2]), list)

    def assertUnchanged(self, v):
        self.assertIs(mitogen.utils.cast(v), v)

    def test_passthrough(self):
        self.assertUnchanged(0)
        self.assertUnchanged(0.0)
        self.assertUnchanged(float('inf'))
        self.assertUnchanged(True)
        self.assertUnchanged(False)
        self.assertUnchanged(None)

    def test_unicode(self):
        self.assertEqual(type(mitogen.utils.cast(u'')), mitogen.core.UnicodeType)
        self.assertEqual(type(mitogen.utils.cast(Unicode())), mitogen.core.UnicodeType)

    def test_bytes(self):
        self.assertEqual(type(mitogen.utils.cast(b'')), mitogen.core.BytesType)
        self.assertEqual(type(mitogen.utils.cast(Bytes())), mitogen.core.BytesType)

    def test_unknown(self):
        self.assertRaises(TypeError, mitogen.utils.cast, set())
        self.assertRaises(TypeError, mitogen.utils.cast, 4j)


if __name__ == '__main__':
    unittest2.main()
