
import unittest2

import mitogen.select

import testlib


class AddTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_receiver(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass()
        select.add(recv)
        self.assertEquals(1, len(select._receivers))
        self.assertEquals(recv, select._receivers[0])
        self.assertEquals(select._put, recv.notify)

    def test_channel(self):
        context = self.router.local()
        chan = mitogen.core.Channel(self.router, context, 1234)
        select = self.klass()
        select.add(chan)
        self.assertEquals(1, len(select._receivers))
        self.assertEquals(chan, select._receivers[0])
        self.assertEquals(select._put, chan.notify)

    def test_subselect_empty(self):
        select = self.klass()
        subselect = self.klass()
        select.add(subselect)
        self.assertEquals(1, len(select._receivers))
        self.assertEquals(subselect, select._receivers[0])
        self.assertEquals(select._put, subselect.notify)

    def test_subselect_nonempty(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass()
        subselect = self.klass()
        subselect.add(recv)

        select.add(subselect)
        self.assertEquals(1, len(select._receivers))
        self.assertEquals(subselect, select._receivers[0])
        self.assertEquals(select._put, subselect.notify)

    def test_subselect_loop_direct(self):
        select = self.klass()
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.add(select))
        self.assertEquals(str(exc), self.klass.loop_msg)

    def test_subselect_loop_indirect(self):
        s0 = self.klass()
        s1 = self.klass()
        s2 = self.klass()

        s0.add(s1)
        s1.add(s2)
        exc = self.assertRaises(mitogen.select.Error,
            lambda: s2.add(s0))
        self.assertEquals(str(exc), self.klass.loop_msg)

    def test_double_add_receiver(self):
        select = self.klass()
        recv = mitogen.core.Receiver(self.router)
        select.add(recv)
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.add(recv))
        self.assertEquals(str(exc), self.klass.owned_msg)

    def test_double_add_subselect(self):
        select = self.klass()
        select2 = self.klass()
        select.add(select2)
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.add(select2))
        self.assertEquals(str(exc), self.klass.owned_msg)


class RemoveTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_empty(self):
        select = self.klass()
        recv = mitogen.core.Receiver(self.router)
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.remove(recv))
        self.assertEquals(str(exc), self.klass.not_present_msg)

    def test_absent(self):
        select = self.klass()
        recv = mitogen.core.Receiver(self.router)
        recv2 = mitogen.core.Receiver(self.router)
        select.add(recv2)
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.remove(recv))
        self.assertEquals(str(exc), self.klass.not_present_msg)

    def test_present(self):
        select = self.klass()
        recv = mitogen.core.Receiver(self.router)
        select.add(recv)
        select.remove(recv)
        self.assertEquals(0, len(select._receivers))
        self.assertEquals(None, recv.notify)


class CloseTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_empty(self):
        select = self.klass()
        select.close()  # No effect.

    def test_one_receiver(self):
        select = self.klass()
        recv = mitogen.core.Receiver(self.router)
        select.add(recv)

        self.assertEquals(1, len(select._receivers))
        self.assertEquals(select._put, recv.notify)

        select.close()
        self.assertEquals(0, len(select._receivers))
        self.assertEquals(None, recv.notify)

    def test_one_subselect(self):
        select = self.klass()
        subselect = self.klass()
        select.add(subselect)

        recv = mitogen.core.Receiver(self.router)
        subselect.add(recv)

        self.assertEquals(1, len(select._receivers))
        self.assertEquals(subselect._put, recv.notify)

        select.close()

        self.assertEquals(0, len(select._receivers))
        self.assertEquals(subselect._put, recv.notify)

        subselect.close()
        self.assertEquals(None, recv.notify)


class EmptyTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_no_receivers(self):
        select = self.klass()
        self.assertTrue(select.empty())

    def test_empty_receiver(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        self.assertTrue(select.empty())

    def test_nonempty_before_add(self):
        recv = mitogen.core.Receiver(self.router)
        recv._on_receive(mitogen.core.Message.pickled('123'))
        select = self.klass([recv])
        self.assertFalse(select.empty())

    def test_nonempty_after_add(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        recv._on_receive(mitogen.core.Message.pickled('123'))
        self.assertFalse(select.empty())


class IterTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_empty(self):
        select = self.klass()
        self.assertEquals([], list(select))

    def test_nonempty(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        msg = mitogen.core.Message.pickled('123')
        recv._on_receive(msg)
        self.assertEquals([msg], list(select))


class OneShotTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_true_removed_after_get(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        msg = mitogen.core.Message.pickled('123')
        recv._on_receive(msg)
        msg_ = select.get()
        self.assertEquals(msg, msg_)
        self.assertEquals(0, len(select._receivers))
        self.assertEquals(None, recv.notify)

    def test_false_persists_after_get(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv], oneshot=False)
        msg = mitogen.core.Message.pickled('123')
        recv._on_receive(msg)

        self.assertEquals(msg, select.get())
        self.assertEquals(1, len(select._receivers))
        self.assertEquals(recv, select._receivers[0])
        self.assertEquals(select._put, recv.notify)


class GetTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.select.Select

    def test_no_receivers(self):
        select = self.klass()
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.get())
        self.assertEquals(str(exc), self.klass.empty_msg)

    def test_timeout_no_receivers(self):
        select = self.klass()
        exc = self.assertRaises(mitogen.select.Error,
            lambda: select.get(timeout=1.0))
        self.assertEquals(str(exc), self.klass.empty_msg)

    def test_zero_timeout(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        self.assertRaises(mitogen.core.TimeoutError,
            lambda: select.get(timeout=0.0))

    def test_timeout(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        self.assertRaises(mitogen.core.TimeoutError,
            lambda: select.get(timeout=0.1))

    def test_nonempty_before_add(self):
        recv = mitogen.core.Receiver(self.router)
        recv._on_receive(mitogen.core.Message.pickled('123'))
        select = self.klass([recv])
        msg = select.get()
        self.assertEquals('123', msg.unpickle())

    def test_nonempty_after_add(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        recv._on_receive(mitogen.core.Message.pickled('123'))
        msg = select.get()
        self.assertEquals('123', msg.unpickle())

    def test_nonempty_receiver_attr_set(self):
        recv = mitogen.core.Receiver(self.router)
        select = self.klass([recv])
        recv._on_receive(mitogen.core.Message.pickled('123'))
        msg = select.get()
        self.assertEquals(msg.receiver, recv)

    def test_drained_by_other_thread(self):
        recv = mitogen.core.Receiver(self.router)
        recv._on_receive(mitogen.core.Message.pickled('123'))
        select = self.klass([recv])
        msg = recv.get()
        self.assertEquals('123', msg.unpickle())
        self.assertRaises(mitogen.core.TimeoutError,
            lambda: select.get(timeout=0.0))


if __name__ == '__main__':
    unittest2.main()
