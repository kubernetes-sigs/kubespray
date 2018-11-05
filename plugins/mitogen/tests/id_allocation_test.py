
import unittest2

import testlib

import mitogen.core
import mitogen.parent


@mitogen.core.takes_econtext
def allocate_an_id(econtext):
    mitogen.parent.upgrade_router(econtext)
    return econtext.router.allocate_id()


class SlaveTest(testlib.RouterMixin, testlib.TestCase):
    def test_slave_allocates_id(self):
        context = self.router.local()
        # Master's allocator named the context 1.
        self.assertEquals(1, context.context_id)

        # First call from slave allocates a block (2..1001)
        id_ = context.call(allocate_an_id)
        self.assertEqual(id_, 2)

        # Second call from slave allocates from block (3..1001)
        id_ = context.call(allocate_an_id)
        self.assertEqual(id_, 3)

        # Subsequent master allocation does not collide
        c2 = self.router.local()
        self.assertEquals(1002, c2.context_id)


if __name__ == '__main__':
    unittest2.main()
