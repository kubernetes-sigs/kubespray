import logging
import subprocess
import time
import zlib

import unittest2

import testlib
import mitogen.master
import mitogen.parent
import mitogen.utils

try:
    import Queue
except ImportError:
    import queue as Queue


def ping():
    return True


@mitogen.core.takes_router
def ping_context(other, router):
    other = mitogen.parent.Context(router, other.context_id)
    other.call(ping)


@mitogen.core.takes_router
def return_router_max_message_size(router):
    return router.max_message_size


def send_n_sized_reply(sender, n):
    sender.send(' ' * n)
    return 123


class SourceVerifyTest(testlib.RouterMixin, unittest2.TestCase):
    def setUp(self):
        super(SourceVerifyTest, self).setUp()
        # Create some children, ping them, and store what their messages look
        # like so we can mess with them later.
        self.child1 = self.router.fork()
        self.child1_msg = self.child1.call_async(ping).get()
        self.child1_stream = self.router._stream_by_id[self.child1.context_id]

        self.child2 = self.router.fork()
        self.child2_msg = self.child2.call_async(ping).get()
        self.child2_stream = self.router._stream_by_id[self.child2.context_id]

    def test_bad_auth_id(self):
        # Deliver a message locally from child2, but using child1's stream.
        log = testlib.LogCapturer()
        log.start()

        # Used to ensure the message was dropped rather than routed after the
        # error is logged.
        recv = mitogen.core.Receiver(self.router)
        self.child2_msg.handle = recv.handle

        self.broker.defer(self.router._async_route,
                          self.child2_msg,
                          in_stream=self.child1_stream)

        # Wait for IO loop to finish everything above.
        self.sync_with_broker()

        # Ensure message wasn't forwarded.
        self.assertTrue(recv.empty())

        # Ensure error was logged.
        expect = 'bad auth_id: got %d via' % (self.child2_msg.auth_id,)
        self.assertTrue(expect in log.stop())

    def test_bad_src_id(self):
        # Deliver a message locally from child2 with the correct auth_id, but
        # the wrong src_id.
        log = testlib.LogCapturer()
        log.start()

        # Used to ensure the message was dropped rather than routed after the
        # error is logged.
        recv = mitogen.core.Receiver(self.router)
        self.child2_msg.handle = recv.handle
        self.child2_msg.src_id = self.child1.context_id

        self.broker.defer(self.router._async_route,
                          self.child2_msg,
                          self.child2_stream)

        # Wait for IO loop to finish everything above.
        self.sync_with_broker()

        # Ensure message wasn't forwarded.
        self.assertTrue(recv.empty())

        # Ensure error was lgoged.
        expect = 'bad src_id: got %d via' % (self.child1_msg.src_id,)
        self.assertTrue(expect in log.stop())


class PolicyTest(testlib.RouterMixin, testlib.TestCase):
    def test_allow_any(self):
        # This guy gets everything.
        recv = mitogen.core.Receiver(self.router)
        recv.to_sender().send(123)
        self.sync_with_broker()
        self.assertFalse(recv.empty())
        self.assertEquals(123, recv.get().unpickle())

    def test_refuse_all(self):
        # Deliver a message locally from child2 with the correct auth_id, but
        # the wrong src_id.
        log = testlib.LogCapturer()
        log.start()

        # This guy never gets anything.
        recv = mitogen.core.Receiver(
            router=self.router,
            policy=(lambda msg, stream: False),
        )

        # This guy becomes the reply_to of our refused message.
        reply_target = mitogen.core.Receiver(self.router)

        # Send the message.
        self.router.route(
            mitogen.core.Message(
                dst_id=mitogen.context_id,
                handle=recv.handle,
                reply_to=reply_target.handle,
            )
        )

        # Wait for IO loop.
        self.sync_with_broker()

        # Verify log.
        expect = '%r: policy refused message: ' % (self.router,)
        self.assertTrue(expect in log.stop())

        # Verify message was not delivered.
        self.assertTrue(recv.empty())

        # Verify CallError received by reply_to target.
        e = self.assertRaises(mitogen.core.CallError,
                              lambda: reply_target.get().unpickle())
        self.assertEquals(e.args[0], self.router.refused_msg)


class CrashTest(testlib.BrokerMixin, unittest2.TestCase):
    # This is testing both Broker's ability to crash nicely, and Router's
    # ability to respond to the crash event.
    klass = mitogen.master.Router

    def _naughty(self):
        raise ValueError('eek')

    def test_shutdown(self):
        router = self.klass(self.broker)

        sem = mitogen.core.Latch()
        router.add_handler(sem.put)

        log = testlib.LogCapturer('mitogen')
        log.start()

        # Force a crash and ensure it wakes up.
        self.broker._loop_once = self._naughty
        self.broker.defer(lambda: None)

        # sem should have received dead message.
        self.assertTrue(sem.get().is_dead)

        # Ensure it was logged.
        expect = '_broker_main() crashed'
        self.assertTrue(expect in log.stop())



class AddHandlerTest(unittest2.TestCase):
    klass = mitogen.master.Router

    def test_invoked_at_shutdown(self):
        router = self.klass()
        queue = Queue.Queue()
        handle = router.add_handler(queue.put)
        router.broker.shutdown()
        self.assertTrue(queue.get(timeout=5).is_dead)


class MessageSizeTest(testlib.BrokerMixin, testlib.TestCase):
    klass = mitogen.master.Router

    def test_local_exceeded(self):
        router = self.klass(broker=self.broker, max_message_size=4096)

        logs = testlib.LogCapturer()
        logs.start()

        # Send message and block for one IO loop, so _async_route can run.
        router.route(mitogen.core.Message.pickled(' '*8192))
        router.broker.defer_sync(lambda: None)

        expect = 'message too large (max 4096 bytes)'
        self.assertTrue(expect in logs.stop())

    def test_local_dead_message(self):
        # Local router should generate dead message when reply_to is set.
        router = self.klass(broker=self.broker, max_message_size=4096)

        logs = testlib.LogCapturer()
        logs.start()

        # Try function call. Receiver should be woken by a dead message sent by
        # router due to message size exceeded.
        child = router.fork()
        e = self.assertRaises(mitogen.core.ChannelError,
            lambda: child.call(zlib.crc32, ' '*8192))
        self.assertEquals(e.args[0], mitogen.core.ChannelError.local_msg)

        expect = 'message too large (max 4096 bytes)'
        self.assertTrue(expect in logs.stop())

    def test_remote_configured(self):
        router = self.klass(broker=self.broker, max_message_size=4096)
        remote = router.fork()
        size = remote.call(return_router_max_message_size)
        self.assertEquals(size, 4096)

    def test_remote_exceeded(self):
        # Ensure new contexts receive a router with the same value.
        router = self.klass(broker=self.broker, max_message_size=4096)
        recv = mitogen.core.Receiver(router)

        logs = testlib.LogCapturer()
        logs.start()

        remote = router.fork()
        remote.call(send_n_sized_reply, recv.to_sender(), 8192)

        expect = 'message too large (max 4096 bytes)'
        self.assertTrue(expect in logs.stop())


class NoRouteTest(testlib.RouterMixin, testlib.TestCase):
    def test_invalid_handle_returns_dead(self):
        # Verify sending a message to an invalid handle yields a dead message
        # from the target context.
        l1 = self.router.fork()
        recv = l1.send_async(mitogen.core.Message(handle=999))
        msg = recv.get(throw_dead=False)
        self.assertEquals(msg.is_dead, True)
        self.assertEquals(msg.src_id, l1.context_id)

        recv = l1.send_async(mitogen.core.Message(handle=999))
        e = self.assertRaises(mitogen.core.ChannelError,
                              lambda: recv.get())
        self.assertEquals(e.args[0], mitogen.core.ChannelError.remote_msg)

    def test_totally_invalid_context_returns_dead(self):
        recv = mitogen.core.Receiver(self.router)
        msg = mitogen.core.Message(
            dst_id=1234,
            handle=1234,
            reply_to=recv.handle,
        )
        self.router.route(msg)
        rmsg = recv.get(throw_dead=False)
        self.assertEquals(rmsg.is_dead, True)
        self.assertEquals(rmsg.src_id, mitogen.context_id)

        self.router.route(msg)
        e = self.assertRaises(mitogen.core.ChannelError,
                              lambda: recv.get())
        self.assertEquals(e.args[0], mitogen.core.ChannelError.local_msg)

    def test_previously_alive_context_returns_dead(self):
        l1 = self.router.fork()
        l1.shutdown(wait=True)
        recv = mitogen.core.Receiver(self.router)
        msg = mitogen.core.Message(
            dst_id=l1.context_id,
            handle=mitogen.core.CALL_FUNCTION,
            reply_to=recv.handle,
        )
        self.router.route(msg)
        rmsg = recv.get(throw_dead=False)
        self.assertEquals(rmsg.is_dead, True)
        self.assertEquals(rmsg.src_id, mitogen.context_id)

        self.router.route(msg)
        e = self.assertRaises(mitogen.core.ChannelError,
                              lambda: recv.get())
        self.assertEquals(e.args[0], mitogen.core.ChannelError.local_msg)


class UnidirectionalTest(testlib.RouterMixin, testlib.TestCase):
    def test_siblings_cant_talk(self):
        self.router.unidirectional = True
        l1 = self.router.fork()
        l2 = self.router.fork()
        logs = testlib.LogCapturer()
        logs.start()
        e = self.assertRaises(mitogen.core.CallError,
                              lambda: l2.call(ping_context, l1))

        msg = 'mitogen.core.ChannelError: Channel closed by remote end.'
        self.assertTrue(msg in str(e))
        self.assertTrue('routing mode prevents forward of ' in logs.stop())

    def test_auth_id_can_talk(self):
        self.router.unidirectional = True
        # One stream has auth_id stamped to that of the master, so it should be
        # treated like a parent.
        l1 = self.router.fork()
        l1s = self.router.stream_by_id(l1.context_id)
        l1s.auth_id = mitogen.context_id
        l1s.is_privileged = True

        l2 = self.router.fork()
        logs = testlib.LogCapturer()
        logs.start()
        e = self.assertRaises(mitogen.core.CallError,
                              lambda: l2.call(ping_context, l1))

        msg = 'mitogen.core.CallError: Refused by policy.'
        self.assertTrue(msg in str(e))
        self.assertTrue('policy refused message: ' in logs.stop())


class EgressIdsTest(testlib.RouterMixin, testlib.TestCase):
    def test_egress_ids_populated(self):
        # Ensure Stream.egress_ids is populated on message reception.
        c1 = self.router.fork()
        stream = self.router.stream_by_id(c1.context_id)
        self.assertEquals(set(), stream.egress_ids)

        c1.call(time.sleep, 0)
        self.assertEquals(set([mitogen.context_id]), stream.egress_ids)


if __name__ == '__main__':
    unittest2.main()
