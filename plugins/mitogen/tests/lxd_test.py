import os

import mitogen
import mitogen.lxd
import mitogen.parent

import unittest2

import testlib


class ConstructorTest(testlib.RouterMixin, testlib.TestCase):
    def test_okay(self):
        lxc_path = testlib.data_path('stubs/lxc.py')
        context = self.router.lxd(
            container='container_name',
            lxc_path=lxc_path,
        )

        argv = eval(context.call(os.getenv, 'ORIGINAL_ARGV'))
        self.assertEquals(argv[0], lxc_path)
        self.assertEquals(argv[1], 'exec')
        self.assertEquals(argv[2], '--mode=noninteractive')
        self.assertEquals(argv[3], 'container_name')

    def test_eof(self):
        e = self.assertRaises(mitogen.parent.EofError,
            lambda: self.router.lxd(
                container='container_name',
                lxc_path='true',
            )
        )
        self.assertTrue(str(e).endswith(mitogen.lxd.Stream.eof_error_hint))


if __name__ == '__main__':
    unittest2.main()
