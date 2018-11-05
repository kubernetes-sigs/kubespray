
import logging
import time

import unittest2

import mitogen.core
import mitogen.master

import testlib


def roundtrip(*args):
    return args

class TwoThreeCompatTest(testlib.RouterMixin, testlib.TestCase):
    if mitogen.core.PY3:
        python_path = 'python2'
    else:
        python_path = 'python3'

    def test_succeeds(self):
        spare = self.router.fork()
        target = self.router.local(python_path=self.python_path)

        spare2, = target.call(roundtrip, spare)
        self.assertEquals(spare.context_id, spare2.context_id)
        self.assertEquals(spare.name, spare2.name)


if __name__ == '__main__':
    unittest2.main()
