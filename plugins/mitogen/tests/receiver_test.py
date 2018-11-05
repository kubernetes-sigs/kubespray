
import unittest2

import mitogen.core
import testlib


def yield_stuff_then_die(sender):
    for x in range(5):
        sender.send(x)
    sender.close()
    return 10


class ConstructorTest(testlib.RouterMixin, testlib.TestCase):
    def test_handle(self):
        recv = mitogen.core.Receiver(self.router)
        self.assertTrue(isinstance(recv.handle, int))
        self.assertTrue(recv.handle > 100)
        self.router.route(
            mitogen.core.Message.pickled(
                'hi',
                dst_id=0,
                handle=recv.handle,
            )
        )
        self.assertEquals('hi', recv.get().unpickle())


class IterationTest(testlib.RouterMixin, testlib.TestCase):
    def test_dead_stops_iteration(self):
        recv = mitogen.core.Receiver(self.router)
        fork = self.router.fork()
        ret = fork.call_async(yield_stuff_then_die, recv.to_sender())
        self.assertEquals(list(range(5)), list(m.unpickle() for m in recv))
        self.assertEquals(10, ret.get().unpickle())


if __name__ == '__main__':
    unittest2.main()
