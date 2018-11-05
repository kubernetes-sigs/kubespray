import errno
import os
import signal
import subprocess
import sys
import tempfile
import time

import mock
import unittest2
import testlib

import mitogen.parent


def wait_for_child(pid, timeout=1.0):
    deadline = time.time() + timeout
    while timeout < time.time():
        try:
            target_pid, status = os.waitpid(pid, os.WNOHANG)
            if target_pid == pid:
                return
        except OSError:
            e = sys.exc_info()[1]
            if e.args[0] == errno.ECHILD:
                return

        time.sleep(0.05)

    assert False, "wait_for_child() timed out"


@mitogen.core.takes_econtext
def call_func_in_sibling(ctx, econtext):
    ctx.call(time.sleep, 99999)


class GetDefaultRemoteNameTest(testlib.TestCase):
    func = staticmethod(mitogen.parent.get_default_remote_name)

    @mock.patch('os.getpid')
    @mock.patch('getpass.getuser')
    @mock.patch('socket.gethostname')
    def test_slashes(self, mock_gethostname, mock_getuser, mock_getpid):
        # Ensure slashes appearing in the remote name are replaced with
        # underscores.
        mock_gethostname.return_value = 'box'
        mock_getuser.return_value = 'ECORP\\Administrator'
        mock_getpid.return_value = 123
        self.assertEquals("ECORP_Administrator@box:123", self.func())


class WstatusToStrTest(testlib.TestCase):
    func = staticmethod(mitogen.parent.wstatus_to_str)

    def test_return_zero(self):
        pid = os.fork()
        if not pid:
            os._exit(0)
        (pid, status), _ = mitogen.core.io_op(os.waitpid, pid, 0)
        self.assertEquals(self.func(status),
                          'exited with return code 0')

    def test_return_one(self):
        pid = os.fork()
        if not pid:
            os._exit(1)
        (pid, status), _ = mitogen.core.io_op(os.waitpid, pid, 0)
        self.assertEquals(
            self.func(status),
            'exited with return code 1'
        )

    def test_sigkill(self):
        pid = os.fork()
        if not pid:
            time.sleep(600)
        os.kill(pid, signal.SIGKILL)
        (pid, status), _ = mitogen.core.io_op(os.waitpid, pid, 0)
        self.assertEquals(
            self.func(status),
            'exited due to signal %s (SIGKILL)' % (int(signal.SIGKILL),)
        )

    # can't test SIGSTOP without POSIX sessions rabbithole


class ReapChildTest(testlib.RouterMixin, testlib.TestCase):
    def test_connect_timeout(self):
        # Ensure the child process is reaped if the connection times out.
        stream = mitogen.parent.Stream(
            router=self.router,
            remote_id=1234,
            old_router=self.router,
            max_message_size=self.router.max_message_size,
            python_path=testlib.data_path('python_never_responds.sh'),
            connect_timeout=0.5,
        )
        self.assertRaises(mitogen.core.TimeoutError,
            lambda: stream.connect()
        )
        wait_for_child(stream.pid)
        e = self.assertRaises(OSError,
            lambda: os.kill(stream.pid, 0)
        )
        self.assertEquals(e.args[0], errno.ESRCH)


class StreamErrorTest(testlib.RouterMixin, testlib.TestCase):
    def test_direct_eof(self):
        e = self.assertRaises(mitogen.core.StreamError,
            lambda: self.router.local(
                python_path='true',
                connect_timeout=3,
            )
        )
        prefix = "EOF on stream; last 300 bytes received: "
        self.assertTrue(e.args[0].startswith(prefix))

    def test_via_eof(self):
        # Verify FD leakage does not keep failed process open.
        local = self.router.fork()
        e = self.assertRaises(mitogen.core.StreamError,
            lambda: self.router.local(
                via=local,
                python_path='true',
                connect_timeout=3,
            )
        )
        s = "EOF on stream; last 300 bytes received: "
        self.assertTrue(s in e.args[0])

    def test_direct_enoent(self):
        e = self.assertRaises(mitogen.core.StreamError,
            lambda: self.router.local(
                python_path='derp',
                connect_timeout=3,
            )
        )
        prefix = 'Child start failed: [Errno 2] No such file or directory'
        self.assertTrue(e.args[0].startswith(prefix))

    def test_via_enoent(self):
        local = self.router.fork()
        e = self.assertRaises(mitogen.core.StreamError,
            lambda: self.router.local(
                via=local,
                python_path='derp',
                connect_timeout=3,
            )
        )
        s = 'Child start failed: [Errno 2] No such file or directory'
        self.assertTrue(s in e.args[0])


class ContextTest(testlib.RouterMixin, unittest2.TestCase):
    def test_context_shutdown(self):
        local = self.router.local()
        pid = local.call(os.getpid)
        local.shutdown(wait=True)
        wait_for_child(pid)
        self.assertRaises(OSError, lambda: os.kill(pid, 0))


class OpenPtyTest(testlib.TestCase):
    func = staticmethod(mitogen.parent.openpty)

    def test_pty_returned(self):
        master_fd, slave_fd = self.func()
        self.assertTrue(isinstance(master_fd, int))
        self.assertTrue(isinstance(slave_fd, int))
        os.close(master_fd)
        os.close(slave_fd)

    @mock.patch('os.openpty')
    def test_max_reached(self, openpty):
        openpty.side_effect = OSError(errno.ENXIO)
        e = self.assertRaises(mitogen.core.StreamError,
                              lambda: self.func())
        msg = mitogen.parent.OPENPTY_MSG % (openpty.side_effect,)
        self.assertEquals(e.args[0], msg)


class TtyCreateChildTest(unittest2.TestCase):
    func = staticmethod(mitogen.parent.tty_create_child)

    def test_dev_tty_open_succeeds(self):
        # In the early days of UNIX, a process that lacked a controlling TTY
        # would acquire one simply by opening an existing TTY. Linux and OS X
        # continue to follow this behaviour, however at least FreeBSD moved to
        # requiring an explicit ioctl(). Linux supports it, but we don't yet
        # use it there and anyway the behaviour will never change, so no point
        # in fixing things that aren't broken. Below we test that
        # getpass-loving apps like sudo and ssh get our slave PTY when they
        # attempt to open /dev/tty, which is what they both do on attempting to
        # read a password.
        tf = tempfile.NamedTemporaryFile()
        try:
            pid, fd, _ = self.func([
                'bash', '-c', 'exec 2>%s; echo hi > /dev/tty' % (tf.name,)
            ])
            deadline = time.time() + 5.0
            for line in mitogen.parent.iter_read([fd], deadline):
                self.assertEquals(mitogen.core.b('hi\n'), line)
                break
            waited_pid, status = os.waitpid(pid, 0)
            self.assertEquals(pid, waited_pid)
            self.assertEquals(0, status)
            self.assertEquals(mitogen.core.b(''), tf.read())
        finally:
            tf.close()


class IterReadTest(unittest2.TestCase):
    func = staticmethod(mitogen.parent.iter_read)

    def make_proc(self):
        args = [testlib.data_path('iter_read_generator.sh')]
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        mitogen.core.set_nonblock(proc.stdout.fileno())
        return proc

    def test_no_deadline(self):
        proc = self.make_proc()
        try:
            reader = self.func([proc.stdout.fileno()])
            for i, chunk in enumerate(reader, 1):
                self.assertEqual(i, int(chunk))
                if i > 3:
                    break
        finally:
            proc.terminate()

    def test_deadline_exceeded_before_call(self):
        proc = self.make_proc()
        reader = self.func([proc.stdout.fileno()], 0)
        try:
            got = []
            try:
                for chunk in reader:
                    got.append(chunk)
                assert 0, 'TimeoutError not raised'
            except mitogen.core.TimeoutError:
                self.assertEqual(len(got), 0)
        finally:
            proc.terminate()

    def test_deadline_exceeded_during_call(self):
        proc = self.make_proc()
        reader = self.func([proc.stdout.fileno()], time.time() + 0.4)
        try:
            got = []
            try:
                for chunk in reader:
                    got.append(chunk)
                assert 0, 'TimeoutError not raised'
            except mitogen.core.TimeoutError:
                # Give a little wiggle room in case of imperfect scheduling.
                # Ideal number should be 9.
                self.assertLess(3, len(got))
                self.assertLess(len(got), 5)
        finally:
            proc.terminate()


class WriteAllTest(unittest2.TestCase):
    func = staticmethod(mitogen.parent.write_all)

    def make_proc(self):
        args = [testlib.data_path('write_all_consumer.sh')]
        proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        mitogen.core.set_nonblock(proc.stdin.fileno())
        return proc

    ten_ms_chunk = (mitogen.core.b('x') * 65535)

    def test_no_deadline(self):
        proc = self.make_proc()
        try:
            self.func(proc.stdin.fileno(), self.ten_ms_chunk)
        finally:
            proc.terminate()

    def test_deadline_exceeded_before_call(self):
        proc = self.make_proc()
        try:
            self.assertRaises(mitogen.core.TimeoutError, (
                lambda: self.func(proc.stdin.fileno(), self.ten_ms_chunk, 0)
            ))
        finally:
            proc.terminate()

    def test_deadline_exceeded_during_call(self):
        proc = self.make_proc()
        try:
            deadline = time.time() + 0.1   # 100ms deadline
            self.assertRaises(mitogen.core.TimeoutError, (
                lambda: self.func(proc.stdin.fileno(),
                                  self.ten_ms_chunk * 100,  # 1s of data
                                  deadline)
            ))
        finally:
            proc.terminate()


class DisconnectTest(testlib.RouterMixin, testlib.TestCase):
    def test_child_disconnected(self):
        # Easy mode: process notices its own directly connected child is
        # disconnected.
        c1 = self.router.fork()
        recv = c1.call_async(time.sleep, 9999)
        c1.shutdown(wait=True)
        e = self.assertRaises(mitogen.core.ChannelError,
            lambda: recv.get())
        self.assertEquals(e.args[0], mitogen.core.ChannelError.local_msg)

    def test_indirect_child_disconnected(self):
        # Achievement unlocked: process notices an indirectly connected child
        # is disconnected.
        c1 = self.router.fork()
        c2 = self.router.fork(via=c1)
        recv = c2.call_async(time.sleep, 9999)
        c2.shutdown(wait=True)
        e = self.assertRaises(mitogen.core.ChannelError,
            lambda: recv.get())
        self.assertEquals(e.args[0], mitogen.core.ChannelError.local_msg)

    def test_indirect_child_intermediary_disconnected(self):
        # Battlefield promotion: process notices indirect child disconnected
        # due to an intermediary child disconnecting.
        c1 = self.router.fork()
        c2 = self.router.fork(via=c1)
        recv = c2.call_async(time.sleep, 9999)
        c1.shutdown(wait=True)
        e = self.assertRaises(mitogen.core.ChannelError,
            lambda: recv.get())
        self.assertEquals(e.args[0], mitogen.core.ChannelError.local_msg)

    def test_near_sibling_disconnected(self):
        # Hard mode: child notices sibling connected to same parent has
        # disconnected.
        c1 = self.router.fork()
        c2 = self.router.fork()

        # Let c1 call functions in c2.
        self.router.stream_by_id(c1.context_id).auth_id = mitogen.context_id
        c1.call(mitogen.parent.upgrade_router)

        recv = c1.call_async(call_func_in_sibling, c2)
        c2.shutdown(wait=True)
        e = self.assertRaises(mitogen.core.CallError,
            lambda: recv.get().unpickle())
        self.assertTrue(e.args[0].startswith(
            'mitogen.core.ChannelError: Channel closed by local end.'
        ))

    def test_far_sibling_disconnected(self):
        # God mode: child of child notices child of child of parent has
        # disconnected.
        c1 = self.router.fork()
        c11 = self.router.fork(via=c1)

        c2 = self.router.fork()
        c22 = self.router.fork(via=c2)

        # Let c1 call functions in c2.
        self.router.stream_by_id(c1.context_id).auth_id = mitogen.context_id
        c11.call(mitogen.parent.upgrade_router)

        recv = c11.call_async(call_func_in_sibling, c22)
        c22.shutdown(wait=True)
        e = self.assertRaises(mitogen.core.CallError,
            lambda: recv.get().unpickle())
        self.assertTrue(e.args[0].startswith(
            'mitogen.core.ChannelError: Channel closed by local end.'
        ))


if __name__ == '__main__':
    unittest2.main()
