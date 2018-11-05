import logging
import time

import unittest2

import mitogen.core
import mitogen.parent
import mitogen.master

import testlib
import plain_old_module


class CrazyType(object):
    pass


def function_that_adds_numbers(x, y):
    return x + y


def function_that_fails(s=''):
    raise plain_old_module.MyError('exception text'+s)


def func_with_bad_return_value():
    return CrazyType()


def func_returns_arg(context):
    return context


def func_accepts_returns_sender(sender):
    sender.send(123)
    sender.close()
    return sender


class TargetClass:

    offset = 100

    @classmethod
    def add_numbers_with_offset(cls, x, y):
        return cls.offset + x + y


class CallFunctionTest(testlib.RouterMixin, testlib.TestCase):

    def setUp(self):
        super(CallFunctionTest, self).setUp()
        self.local = self.router.fork()

    def test_succeeds(self):
        self.assertEqual(3, self.local.call(function_that_adds_numbers, 1, 2))

    def test_succeeds_class_method(self):
        self.assertEqual(
            self.local.call(TargetClass.add_numbers_with_offset, 1, 2),
            103,
        )

    def test_crashes(self):
        exc = self.assertRaises(mitogen.core.CallError,
            lambda: self.local.call(function_that_fails))

        s = str(exc)
        etype, _, s = s.partition(': ')
        self.assertEqual(etype, 'plain_old_module.MyError')

        msg, _, s = s.partition('\n')
        self.assertEqual(msg, 'exception text')

        # Traceback
        self.assertGreater(len(s), 0)

    def test_bad_return_value(self):
        exc = self.assertRaises(mitogen.core.StreamError,
            lambda: self.local.call(func_with_bad_return_value))
        self.assertEquals(
                exc.args[0],
                "cannot unpickle '%s'/'CrazyType'" % (__name__,),
        )

    def test_aborted_on_local_context_disconnect(self):
        stream = self.router._stream_by_id[self.local.context_id]
        self.broker.stop_receive(stream)
        recv = self.local.call_async(time.sleep, 120)
        self.broker.defer(stream.on_disconnect, self.broker)
        exc = self.assertRaises(mitogen.core.ChannelError,
            lambda: recv.get())
        self.assertEquals(exc.args[0], mitogen.core.ChannelError.local_msg)

    def test_aborted_on_local_broker_shutdown(self):
        stream = self.router._stream_by_id[self.local.context_id]
        recv = self.local.call_async(time.sleep, 120)
        time.sleep(0.05)  # Ensure GIL is released
        self.broker.shutdown()
        exc = self.assertRaises(mitogen.core.ChannelError,
            lambda: recv.get())
        self.assertEquals(exc.args[0], mitogen.core.ChannelError.local_msg)

    def test_accepts_returns_context(self):
        context = self.local.call(func_returns_arg, self.local)
        # Unpickling now deduplicates Context instances.
        self.assertIs(context, self.local)
        self.assertEqual(context.context_id, self.local.context_id)
        self.assertEqual(context.name, self.local.name)

    def test_accepts_returns_sender(self):
        recv = mitogen.core.Receiver(self.router)
        sender = recv.to_sender()
        sender2 = self.local.call(func_accepts_returns_sender, sender)
        self.assertEquals(sender.context.context_id,
                          sender2.context.context_id)
        self.assertEquals(sender.dst_handle, sender2.dst_handle)
        self.assertEquals(123, recv.get().unpickle())
        self.assertRaises(mitogen.core.ChannelError,
                          lambda: recv.get().unpickle())


class CallChainTest(testlib.RouterMixin, testlib.TestCase):
    # Verify mitogen_chain functionality.
    klass = mitogen.parent.CallChain

    def setUp(self):
        super(CallChainTest, self).setUp()
        self.local = self.router.fork()

    def test_subsequent_calls_produce_same_error(self):
        chain = self.klass(self.local, pipelined=True)
        self.assertEquals('xx', chain.call(func_returns_arg, 'xx'))
        chain.call_no_reply(function_that_fails, 'x1')
        e1 = self.assertRaises(mitogen.core.CallError,
            lambda: chain.call(function_that_fails, 'x2'))
        e2 = self.assertRaises(mitogen.core.CallError,
            lambda: chain.call(func_returns_arg, 'x3'))
        self.assertEquals(str(e1), str(e2))

    def test_unrelated_overlapping_failed_chains(self):
        c1 = self.klass(self.local, pipelined=True)
        c2 = self.klass(self.local, pipelined=True)
        c1.call_no_reply(function_that_fails, 'c1')
        self.assertEquals('yes', c2.call(func_returns_arg, 'yes'))
        self.assertRaises(mitogen.core.CallError,
            lambda: c1.call(func_returns_arg, 'yes'))

    def test_reset(self):
        c1 = self.klass(self.local, pipelined=True)
        c1.call_no_reply(function_that_fails, 'x1')
        e1 = self.assertRaises(mitogen.core.CallError,
            lambda: c1.call(function_that_fails, 'x2'))
        c1.reset()
        self.assertEquals('x3', c1.call(func_returns_arg, 'x3'))


if __name__ == '__main__':
    unittest2.main()
