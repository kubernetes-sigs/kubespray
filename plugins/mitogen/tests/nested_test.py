import os

import unittest2

import testlib


class NestedTest(testlib.RouterMixin, testlib.TestCase):
    def test_nested(self):
        context = None
        for x in range(1, 11):
            context = self.router.local(via=context, name='local%d' % x)

        pid = context.call(os.getpid)
        self.assertIsInstance(pid, int)


if __name__ == '__main__':
    unittest2.main()
