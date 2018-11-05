import os

import mitogen
import mitogen.lxc

import unittest2

import testlib


def has_subseq(seq, subseq):
    return any(seq[x:x+len(subseq)] == subseq for x in range(0, len(seq)))


class ConstructorTest(testlib.RouterMixin, testlib.TestCase):
    lxc_attach_path = testlib.data_path('stubs/lxc-attach.py')

    def test_okay(self):
        context = self.router.lxc(
            container='container_name',
            lxc_attach_path=self.lxc_attach_path,
        )

        argv = eval(context.call(os.getenv, 'ORIGINAL_ARGV'))
        self.assertEquals(argv[0], self.lxc_attach_path)
        self.assertTrue('--clear-env' in argv)
        self.assertTrue(has_subseq(argv, ['--name', 'container_name']))

    def test_eof(self):
        e = self.assertRaises(mitogen.parent.EofError,
            lambda: self.router.lxc(
                container='container_name',
                lxc_attach_path='true',
            )
        )
        self.assertTrue(str(e).endswith(mitogen.lxc.Stream.eof_error_hint))


if __name__ == '__main__':
    unittest2.main()
