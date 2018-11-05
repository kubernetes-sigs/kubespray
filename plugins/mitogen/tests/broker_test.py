
import threading

import unittest2

import testlib

import mitogen.core


class DeferSyncTest(testlib.TestCase):
    klass = mitogen.core.Broker

    def test_okay(self):
        broker = self.klass()
        try:
            th = broker.defer_sync(lambda: threading.currentThread())
            self.assertEquals(th, broker._thread)
        finally:
            broker.shutdown()

    def test_exception(self):
        broker = self.klass()
        try:
            self.assertRaises(ValueError,
                broker.defer_sync, lambda: int('dave'))
        finally:
            broker.shutdown()


if __name__ == '__main__':
    unittest2.main()
