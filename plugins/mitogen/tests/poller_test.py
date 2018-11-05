
import errno
import os
import select
import socket
import sys
import time

import unittest2

import mitogen.core
import mitogen.parent

import testlib


class SockMixin(object):
    def tearDown(self):
        self.close_socks()
        super(SockMixin, self).tearDown()

    def setUp(self):
        super(SockMixin, self).setUp()
        self._setup_socks()

    def _setup_socks(self):
        # "left" and "right" side of two socket pairs. We use sockets instead
        # of pipes since the same process can manipulate transmit/receive
        # buffers on both sides (bidirectional IO), making it easier to test
        # combinations of readability/writeability on the one side of a single
        # file object.
        self.l1_sock, self.r1_sock = socket.socketpair()
        self.l1 = self.l1_sock.fileno()
        self.r1 = self.r1_sock.fileno()

        self.l2_sock, self.r2_sock = socket.socketpair()
        self.l2 = self.l2_sock.fileno()
        self.r2 = self.r2_sock.fileno()
        for fd in self.l1, self.r1, self.l2, self.r2:
            mitogen.core.set_nonblock(fd)

    def fill(self, fd):
        """Make `fd` unwriteable."""
        while True:
            try:
                os.write(fd, 'x'*4096)
            except OSError:
                e = sys.exc_info()[1]
                if e.args[0] == errno.EAGAIN:
                    return
                raise

    def drain(self, fd):
        """Make `fd` unreadable."""
        while True:
            try:
                if not os.read(fd, 4096):
                    return
            except OSError:
                e = sys.exc_info()[1]
                if e.args[0] == errno.EAGAIN:
                    return
                raise

    def close_socks(self):
        for sock in self.l1_sock, self.r1_sock, self.l2_sock, self.r2_sock:
            sock.close()


class PollerMixin(object):
    klass = None

    def setUp(self):
        super(PollerMixin, self).setUp()
        self.p = self.klass()

    def tearDown(self):
        self.p.close()
        super(PollerMixin, self).tearDown()


class ReceiveStateMixin(PollerMixin, SockMixin):
    def test_start_receive_adds_reader(self):
        self.p.start_receive(self.l1)
        self.assertEquals([(self.l1, self.l1)], self.p.readers)
        self.assertEquals([], self.p.writers)

    def test_start_receive_adds_reader_data(self):
        data = object()
        self.p.start_receive(self.l1, data=data)
        self.assertEquals([(self.l1, data)], self.p.readers)
        self.assertEquals([], self.p.writers)

    def test_stop_receive(self):
        self.p.start_receive(self.l1)
        self.p.stop_receive(self.l1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([], self.p.writers)

    def test_stop_receive_dup(self):
        self.p.start_receive(self.l1)
        self.p.stop_receive(self.l1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([], self.p.writers)
        self.p.stop_receive(self.l1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([], self.p.writers)

    def test_stop_receive_noexist(self):
        p = self.klass()
        p.stop_receive(123)  # should not fail
        self.assertEquals([], p.readers)
        self.assertEquals([], self.p.writers)


class TransmitStateMixin(PollerMixin, SockMixin):
    def test_start_transmit_adds_writer(self):
        self.p.start_transmit(self.r1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([(self.r1, self.r1)], self.p.writers)

    def test_start_transmit_adds_writer_data(self):
        data = object()
        self.p.start_transmit(self.r1, data=data)
        self.assertEquals([], self.p.readers)
        self.assertEquals([(self.r1, data)], self.p.writers)

    def test_stop_transmit(self):
        self.p.start_transmit(self.r1)
        self.p.stop_transmit(self.r1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([], self.p.writers)

    def test_stop_transmit_dup(self):
        self.p.start_transmit(self.r1)
        self.p.stop_transmit(self.r1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([], self.p.writers)
        self.p.stop_transmit(self.r1)
        self.assertEquals([], self.p.readers)
        self.assertEquals([], self.p.writers)

    def test_stop_transmit_noexist(self):
        p = self.klass()
        p.stop_receive(123)  # should not fail
        self.assertEquals([], p.readers)
        self.assertEquals([], self.p.writers)


class CloseMixin(PollerMixin):
    def test_single_close(self):
        self.p.close()

    def test_double_close(self):
        self.p.close()
        self.p.close()


class PollMixin(PollerMixin):
    def test_empty_zero_timeout(self):
        t0 = time.time()
        self.assertEquals([], list(self.p.poll(0)))
        self.assertTrue((time.time() - t0) < .1)  # vaguely reasonable

    def test_empty_small_timeout(self):
        t0 = time.time()
        self.assertEquals([], list(self.p.poll(.2)))
        self.assertTrue((time.time() - t0) >= .2)


class ReadableMixin(PollerMixin, SockMixin):
    def test_unreadable(self):
        self.p.start_receive(self.l1)
        self.assertEquals([], list(self.p.poll(0)))

    def test_readable_before_add(self):
        self.fill(self.r1)
        self.p.start_receive(self.l1)
        self.assertEquals([self.l1], list(self.p.poll(0)))

    def test_readable_after_add(self):
        self.p.start_receive(self.l1)
        self.fill(self.r1)
        self.assertEquals([self.l1], list(self.p.poll(0)))

    def test_readable_then_unreadable(self):
        self.fill(self.r1)
        self.p.start_receive(self.l1)
        self.assertEquals([self.l1], list(self.p.poll(0)))
        self.drain(self.l1)
        self.assertEquals([], list(self.p.poll(0)))

    def test_readable_data(self):
        data = object()
        self.fill(self.r1)
        self.p.start_receive(self.l1, data=data)
        self.assertEquals([data], list(self.p.poll(0)))

    def test_double_readable_data(self):
        data1 = object()
        data2 = object()
        self.fill(self.r1)
        self.p.start_receive(self.l1, data=data1)
        self.fill(self.r2)
        self.p.start_receive(self.l2, data=data2)
        self.assertEquals(set([data1, data2]), set(self.p.poll(0)))


class WriteableMixin(PollerMixin, SockMixin):
    def test_writeable(self):
        self.p.start_transmit(self.r1)
        self.assertEquals([self.r1], list(self.p.poll(0)))

    def test_writeable_data(self):
        data = object()
        self.p.start_transmit(self.r1, data=data)
        self.assertEquals([data], list(self.p.poll(0)))

    def test_unwriteable_before_add(self):
        self.fill(self.r1)
        self.p.start_transmit(self.r1)
        self.assertEquals([], list(self.p.poll(0)))

    def test_unwriteable_after_add(self):
        self.p.start_transmit(self.r1)
        self.fill(self.r1)
        self.assertEquals([], list(self.p.poll(0)))

    def test_unwriteable_then_writeable(self):
        self.fill(self.r1)
        self.p.start_transmit(self.r1)
        self.assertEquals([], list(self.p.poll(0)))
        self.drain(self.l1)
        self.assertEquals([self.r1], list(self.p.poll(0)))

    def test_double_unwriteable_then_Writeable(self):
        self.fill(self.r1)
        self.p.start_transmit(self.r1)

        self.fill(self.r2)
        self.p.start_transmit(self.r2)

        self.assertEquals([], list(self.p.poll(0)))

        self.drain(self.l1)
        self.assertEquals([self.r1], list(self.p.poll(0)))

        self.drain(self.l2)
        self.assertEquals(set([self.r1, self.r2]), set(self.p.poll(0)))


class MutateDuringYieldMixin(PollerMixin, SockMixin):
    # verify behaviour when poller contents is modified in the middle of
    # poll() output generation.

    def test_one_readable_removed_before_yield(self):
        self.fill(self.l1)
        self.p.start_receive(self.r1)
        p = self.p.poll(0)
        self.p.stop_receive(self.r1)
        self.assertEquals([], list(p))

    def test_one_writeable_removed_before_yield(self):
        self.p.start_transmit(self.r1)
        p = self.p.poll(0)
        self.p.stop_transmit(self.r1)
        self.assertEquals([], list(p))

    def test_one_readable_readded_before_yield(self):
        # fd removed, closed, another fd opened, gets same fd number, re-added.
        # event fires for wrong underlying object.
        self.fill(self.l1)
        self.p.start_receive(self.r1)
        p = self.p.poll(0)
        self.p.stop_receive(self.r1)
        self.p.start_receive(self.r1)
        self.assertEquals([], list(p))

    def test_one_readable_readded_during_yield(self):
        self.fill(self.l1)
        self.p.start_receive(self.r1)

        self.fill(self.l2)
        self.p.start_receive(self.r2)

        p = self.p.poll(0)

        # figure out which one is consumed and which is still to-read.
        consumed = next(p)
        ready = (self.r1, self.r2)[consumed == self.r1]

        # now remove and re-add the one that hasn't been read yet.
        self.p.stop_receive(ready)
        self.p.start_receive(ready)

        # the start_receive() may be for a totally new underlying file object,
        # the live loop iteration must not yield any buffered readiness event.
        self.assertEquals([], list(p))


class FileClosedMixin(PollerMixin, SockMixin):
    # Verify behaviour when a registered file object is closed in various
    # scenarios, without first calling stop_receive()/stop_transmit().

    def test_writeable_then_closed(self):
        self.p.start_transmit(self.r1)
        self.assertEquals([self.r1], list(self.p.poll(0)))
        self.close_socks()
        try:
            self.assertEquals([], list(self.p.poll(0)))
        except select.error:
            # a crash is also reasonable here.
            pass

    def test_writeable_closed_before_yield(self):
        self.p.start_transmit(self.r1)
        p = self.p.poll(0)
        self.close_socks()
        try:
            self.assertEquals([], list(p))
        except select.error:
            # a crash is also reasonable here.
            pass

    def test_readable_then_closed(self):
        self.fill(self.l1)
        self.p.start_receive(self.r1)
        self.assertEquals([self.r1], list(self.p.poll(0)))
        self.close_socks()
        try:
            self.assertEquals([], list(self.p.poll(0)))
        except select.error:
            # a crash is also reasonable here.
            pass

    def test_readable_closed_before_yield(self):
        self.fill(self.l1)
        self.p.start_receive(self.r1)
        p = self.p.poll(0)
        self.close_socks()
        try:
            self.assertEquals([], list(p))
        except select.error:
            # a crash is also reasonable here.
            pass


class DistinctDataMixin(PollerMixin, SockMixin):
    # Verify different data is yielded for the same FD according to the event
    # being raised.

    def test_one_distinct(self):
        rdata = object()
        wdata = object()
        self.p.start_receive(self.r1, data=rdata)
        self.p.start_transmit(self.r1, data=wdata)

        self.assertEquals([wdata], list(self.p.poll(0)))
        self.fill(self.l1)  # r1 is now readable and writeable.
        self.assertEquals(set([rdata, wdata]), set(self.p.poll(0)))


class AllMixin(ReceiveStateMixin,
               TransmitStateMixin,
               ReadableMixin,
               WriteableMixin,
               MutateDuringYieldMixin,
               FileClosedMixin,
               DistinctDataMixin,
               PollMixin,
               CloseMixin):
    """
    Helper to avoid cutpasting mixin names below.
    """


@unittest2.skipIf(condition=not hasattr(select, 'select'),
                  reason='select.select() not supported')
class SelectTest(AllMixin, testlib.TestCase):
    klass = mitogen.core.Poller


@unittest2.skipIf(condition=not hasattr(select, 'kqueue'),
                  reason='select.kqueue() not supported')
class KqueueTest(AllMixin, testlib.TestCase):
    klass = mitogen.parent.KqueuePoller


@unittest2.skipIf(condition=not hasattr(select, 'epoll'),
                  reason='select.epoll() not supported')
class EpollTest(AllMixin, testlib.TestCase):
    klass = mitogen.parent.EpollPoller


if __name__ == '__main__':
    unittest2.main()
