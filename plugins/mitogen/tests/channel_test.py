import unittest2

import mitogen.core
import testlib


class ConstructorTest(testlib.RouterMixin, testlib.TestCase):
    def test_constructor(self):
        # issue 32
        l1 = self.router.local()
        chan = mitogen.core.Channel(self.router, l1, 123)
        self.assertEqual(chan.router, self.router)
        self.assertEqual(chan.context, l1)
        self.assertEqual(chan.dst_handle, 123)
        self.assertIsNotNone(chan.handle)
        self.assertGreater(chan.handle, 0)


if __name__ == '__main__':
    unittest2.main()
