# Copyright 2017, David Wilson
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
This module defines functionality common to master and parent processes. It is
sent to any child context that is due to become a parent, due to recursive
connection.
"""

import codecs
import errno
import fcntl
import getpass
import inspect
import logging
import os
import signal
import socket
import subprocess
import sys
import termios
import textwrap
import threading
import time
import zlib

# Absolute imports for <2.5.
select = __import__('select')

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from functools import lru_cache
except ImportError:
    from mitogen.compat.functools import lru_cache

import mitogen.core
from mitogen.core import b
from mitogen.core import LOG
from mitogen.core import IOLOG


IS_WSL = 'Microsoft' in os.uname()[2]
itervalues = getattr(dict, 'itervalues', dict.values)

if mitogen.core.PY3:
    xrange = range

try:
    SC_OPEN_MAX = os.sysconf('SC_OPEN_MAX')
except:
    SC_OPEN_MAX = 1024

OPENPTY_MSG = (
    "Failed to create a PTY: %s. It is likely the maximum number of PTYs has "
    "been reached. Consider increasing the 'kern.tty.ptmx_max' sysctl on OS "
    "X, the 'kernel.pty.max' sysctl on Linux, or modifying your configuration "
    "to avoid PTY use."
)

SYS_EXECUTABLE_MSG = (
    "The Python sys.executable variable is unset, indicating Python was "
    "unable to determine its original program name. Unless explicitly "
    "configured otherwise, child contexts will be started using "
    "'/usr/bin/python'"
)
_sys_executable_warning_logged = False

SIGNAL_BY_NUM = dict(
    (getattr(signal, name), name)
    for name in sorted(vars(signal), reverse=True)
    if name.startswith('SIG') and not name.startswith('SIG_')
)


def get_log_level():
    return (LOG.level or logging.getLogger().level or logging.INFO)


def get_sys_executable():
    """
    Return :data:`sys.executable` if it is set, otherwise return
    ``"/usr/bin/python"`` and log a warning.
    """
    if sys.executable:
        return sys.executable

    global _sys_executable_warning_logged
    if not _sys_executable_warning_logged:
        LOG.warn(SYS_EXECUTABLE_MSG)
        _sys_executable_warning_logged = True

    return '/usr/bin/python'


def get_core_source():
    """
    In non-masters, simply fetch the cached mitogen.core source code via the
    import mechanism. In masters, this function is replaced with a version that
    performs minification directly.
    """
    return inspect.getsource(mitogen.core)


def get_default_remote_name():
    """
    Return the default name appearing in argv[0] of remote machines.
    """
    s = u'%s@%s:%d'
    s %= (getpass.getuser(), socket.gethostname(), os.getpid())
    # In mixed UNIX/Windows environments, the username may contain slashes.
    return s.translate({
        ord(u'\\'): ord(u'_'),
        ord(u'/'): ord(u'_')
    })


def is_immediate_child(msg, stream):
    """
    Handler policy that requires messages to arrive only from immediately
    connected children.
    """
    return msg.src_id == stream.remote_id


def flags(names):
    """Return the result of ORing a set of (space separated) :py:mod:`termios`
    module constants together."""
    return sum(getattr(termios, name, 0)
               for name in names.split())


def cfmakeraw(tflags):
    """Given a list returned by :py:func:`termios.tcgetattr`, return a list
    modified in a manner similar to the `cfmakeraw()` C library function, but
    additionally disabling local echo."""
    # BSD: https://github.com/freebsd/freebsd/blob/master/lib/libc/gen/termios.c#L162
    # Linux: https://github.com/lattera/glibc/blob/master/termios/cfmakeraw.c#L20
    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = tflags
    iflag &= ~flags('IMAXBEL IXOFF INPCK BRKINT PARMRK ISTRIP INLCR ICRNL IXON IGNPAR')
    iflag &= ~flags('IGNBRK BRKINT PARMRK')
    oflag &= ~flags('OPOST')
    lflag &= ~flags('ECHO ECHOE ECHOK ECHONL ICANON ISIG IEXTEN NOFLSH TOSTOP PENDIN')
    cflag &= ~flags('CSIZE PARENB')
    cflag |= flags('CS8 CREAD')
    return [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]


def disable_echo(fd):
    old = termios.tcgetattr(fd)
    new = cfmakeraw(old)
    flags = getattr(termios, 'TCSASOFT', 0)
    if not IS_WSL:
        # issue #319: Windows Subsystem for Linux as of July 2018 throws EINVAL
        # if TCSAFLUSH is specified.
        flags |= termios.TCSAFLUSH
    termios.tcsetattr(fd, flags, new)


def close_nonstandard_fds():
    for fd in xrange(3, SC_OPEN_MAX):
        try:
            os.close(fd)
        except OSError:
            pass


def create_socketpair():
    """
    Create a :func:`socket.socketpair` to use for use as a child process's UNIX
    stdio channels. As socket pairs are bidirectional, they are economical on
    file descriptor usage as the same descriptor can be used for ``stdin`` and
    ``stdout``. As they are sockets their buffers are tunable, allowing large
    buffers to be configured in order to improve throughput for file transfers
    and reduce :class:`mitogen.core.Broker` IO loop iterations.
    """
    parentfp, childfp = socket.socketpair()
    parentfp.setsockopt(socket.SOL_SOCKET,
                        socket.SO_SNDBUF,
                        mitogen.core.CHUNK_SIZE)
    childfp.setsockopt(socket.SOL_SOCKET,
                       socket.SO_RCVBUF,
                       mitogen.core.CHUNK_SIZE)
    return parentfp, childfp


def detach_popen(*args, **kwargs):
    """
    Use :class:`subprocess.Popen` to construct a child process, then hack the
    Popen so that it forgets the child it created, allowing it to survive a
    call to Popen.__del__.

    If the child process is not detached, there is a race between it exitting
    and __del__ being called. If it exits before __del__ runs, then __del__'s
    call to :func:`os.waitpid` will capture the one and only exit event
    delivered to this process, causing later 'legitimate' calls to fail with
    ECHILD.

    :returns:
        Process ID of the new child.
    """
    # This allows Popen() to be used for e.g. graceful post-fork error
    # handling, without tying the surrounding code into managing a Popen
    # object, which isn't possible for at least :mod:`mitogen.fork`. This
    # should be replaced by a swappable helper class in a future version.
    proc = subprocess.Popen(*args, **kwargs)
    proc._child_created = False
    return proc.pid


def create_child(args, merge_stdio=False, stderr_pipe=False, preexec_fn=None):
    """
    Create a child process whose stdin/stdout is connected to a socket.

    :param args:
        Argument vector for execv() call.
    :param bool merge_stdio:
        If :data:`True`, arrange for `stderr` to be connected to the `stdout`
        socketpair, rather than inherited from the parent process. This may be
        necessary to ensure that not TTY is connected to any stdio handle, for
        instance when using LXC.
    :param bool stderr_pipe:
        If :data:`True` and `merge_stdio` is :data:`False`, arrange for
        `stderr` to be connected to a separate pipe, to allow any ongoing debug
        logs generated by e.g. SSH to be outpu as the session progresses,
        without interfering with `stdout`.
    :returns:
        `(pid, socket_obj, :data:`None` or pipe_fd)`
    """
    parentfp, childfp = create_socketpair()
    # When running under a monkey patches-enabled gevent, the socket module
    # yields file descriptors who already have O_NONBLOCK, which is
    # persisted across fork, totally breaking Python. Therefore, drop
    # O_NONBLOCK from Python's future stdin fd.
    mitogen.core.set_block(childfp.fileno())

    stderr_r = None
    extra = {}
    if merge_stdio:
        extra = {'stderr': childfp}
    elif stderr_pipe:
        stderr_r, stderr_w = os.pipe()
        mitogen.core.set_cloexec(stderr_r)
        mitogen.core.set_cloexec(stderr_w)
        extra = {'stderr': stderr_w}

    pid = detach_popen(
        args=args,
        stdin=childfp,
        stdout=childfp,
        close_fds=True,
        preexec_fn=preexec_fn,
        **extra
    )
    if stderr_pipe:
        os.close(stderr_w)
    childfp.close()
    # Decouple the socket from the lifetime of the Python socket object.
    fd = os.dup(parentfp.fileno())
    parentfp.close()

    LOG.debug('create_child() child %d fd %d, parent %d, cmd: %s',
              pid, fd, os.getpid(), Argv(args))
    return pid, fd, stderr_r


def _acquire_controlling_tty():
    os.setsid()
    if sys.platform == 'linux2':
        # On Linux, the controlling tty becomes the first tty opened by a
        # process lacking any prior tty.
        os.close(os.open(os.ttyname(2), os.O_RDWR))
    if hasattr(termios, 'TIOCSCTTY'):
        # On BSD an explicit ioctl is required. For some inexplicable reason,
        # Python 2.6 on Travis also requires it.
        fcntl.ioctl(2, termios.TIOCSCTTY)


def openpty():
    """
    Call :func:`os.openpty`, raising a descriptive error if the call fails.

    :raises mitogen.core.StreamError:
        Creating a PTY failed.
    :returns:
        See :func`os.openpty`.
    """
    try:
        return os.openpty()
    except OSError:
        e = sys.exc_info()[1]
        raise mitogen.core.StreamError(OPENPTY_MSG, e)


def tty_create_child(args):
    """
    Return a file descriptor connected to the master end of a pseudo-terminal,
    whose slave end is connected to stdin/stdout/stderr of a new child process.
    The child is created such that the pseudo-terminal becomes its controlling
    TTY, ensuring access to /dev/tty returns a new file descriptor open on the
    slave end.

    :param list args:
        :py:func:`os.execl` argument list.

    :returns:
        `(pid, tty_fd, None)`
    """
    master_fd, slave_fd = openpty()
    mitogen.core.set_block(slave_fd)
    disable_echo(master_fd)
    disable_echo(slave_fd)

    pid = detach_popen(
        args=args,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=_acquire_controlling_tty,
        close_fds=True,
    )

    os.close(slave_fd)
    LOG.debug('tty_create_child() child %d fd %d, parent %d, cmd: %s',
              pid, master_fd, os.getpid(), Argv(args))
    return pid, master_fd, None


def hybrid_tty_create_child(args):
    """
    Like :func:`tty_create_child`, except attach stdin/stdout to a socketpair
    like :func:`create_child`, but leave stderr and the controlling TTY
    attached to a TTY.

    :param list args:
        :py:func:`os.execl` argument list.

    :returns:
        `(pid, socketpair_fd, tty_fd)`
    """
    master_fd, slave_fd = openpty()
    parentfp, childfp = create_socketpair()

    mitogen.core.set_block(slave_fd)
    mitogen.core.set_block(childfp)
    disable_echo(master_fd)
    disable_echo(slave_fd)
    pid = detach_popen(
        args=args,
        stdin=childfp,
        stdout=childfp,
        stderr=slave_fd,
        preexec_fn=_acquire_controlling_tty,
        close_fds=True,
    )

    os.close(slave_fd)
    childfp.close()
    # Decouple the socket from the lifetime of the Python socket object.
    stdio_fd = os.dup(parentfp.fileno())
    parentfp.close()

    LOG.debug('hybrid_tty_create_child() pid=%d stdio=%d, tty=%d, cmd: %s',
              pid, stdio_fd, master_fd, Argv(args))
    return pid, stdio_fd, master_fd


def write_all(fd, s, deadline=None):
    """Arrange for all of bytestring `s` to be written to the file descriptor
    `fd`.

    :param int fd:
        File descriptor to write to.
    :param bytes s:
        Bytestring to write to file descriptor.
    :param float deadline:
        If not :data:`None`, absolute UNIX timestamp after which timeout should
        occur.

    :raises mitogen.core.TimeoutError:
        Bytestring could not be written entirely before deadline was exceeded.
    :raises mitogen.parent.EofError:
        Stream indicated EOF, suggesting the child process has exitted.
    :raises mitogen.core.StreamError:
        File descriptor was disconnected before write could complete.
    """
    timeout = None
    written = 0
    poller = PREFERRED_POLLER()
    poller.start_transmit(fd)

    try:
        while written < len(s):
            if deadline is not None:
                timeout = max(0, deadline - time.time())
            if timeout == 0:
                raise mitogen.core.TimeoutError('write timed out')

            if mitogen.core.PY3:
                window = memoryview(s)[written:]
            else:
                window = buffer(s, written)

            for fd in poller.poll(timeout):
                n, disconnected = mitogen.core.io_op(os.write, fd, window)
                if disconnected:
                    raise EofError('EOF on stream during write')

                written += n
    finally:
        poller.close()


def iter_read(fds, deadline=None):
    """Return a generator that arranges for up to 4096-byte chunks to be read
    at a time from the file descriptor `fd` until the generator is destroyed.

    :param int fd:
        File descriptor to read from.
    :param float deadline:
        If not :data:`None`, an absolute UNIX timestamp after which timeout
        should occur.

    :raises mitogen.core.TimeoutError:
        Attempt to read beyond deadline.
    :raises mitogen.parent.EofError:
        All streams indicated EOF, suggesting the child process has exitted.
    :raises mitogen.core.StreamError:
        Attempt to read past end of file.
    """
    poller = PREFERRED_POLLER()
    for fd in fds:
        poller.start_receive(fd)

    bits = []
    timeout = None
    try:
        while poller.readers:
            if deadline is not None:
                timeout = max(0, deadline - time.time())
                if timeout == 0:
                    break

            for fd in poller.poll(timeout):
                s, disconnected = mitogen.core.io_op(os.read, fd, 4096)
                if disconnected or not s:
                    IOLOG.debug('iter_read(%r) -> disconnected', fd)
                    poller.stop_receive(fd)
                else:
                    IOLOG.debug('iter_read(%r) -> %r', fd, s)
                    bits.append(s)
                    yield s
    finally:
        poller.close()

    if not poller.readers:
        raise EofError(u'EOF on stream; last 300 bytes received: %r' %
                       (b('').join(bits)[-300:].decode('latin1'),))

    raise mitogen.core.TimeoutError('read timed out')


def discard_until(fd, s, deadline):
    """Read chunks from `fd` until one is encountered that ends with `s`. This
    is used to skip output produced by ``/etc/profile``, ``/etc/motd`` and
    mandatory SSH banners while waiting for :attr:`Stream.EC0_MARKER` to
    appear, indicating the first stage is ready to receive the compressed
    :mod:`mitogen.core` source.

    :param int fd:
        File descriptor to read from.
    :param bytes s:
        Marker string to discard until encountered.
    :param float deadline:
        Absolute UNIX timestamp after which timeout should occur.

    :raises mitogen.core.TimeoutError:
        Attempt to read beyond deadline.
    :raises mitogen.parent.EofError:
        All streams indicated EOF, suggesting the child process has exitted.
    :raises mitogen.core.StreamError:
        Attempt to read past end of file.
    """
    for buf in iter_read([fd], deadline):
        if IOLOG.level == logging.DEBUG:
            for line in buf.splitlines():
                IOLOG.debug('discard_until: discarding %r', line)
        if buf.endswith(s):
            return


def _upgrade_broker(broker):
    """
    Extract the poller state from Broker and replace it with the industrial
    strength poller for this OS. Must run on the Broker thread.
    """
    # This function is deadly! The act of calling start_receive() generates log
    # messages which must be silenced as the upgrade progresses, otherwise the
    # poller state will change as it is copied, resulting in write fds that are
    # lost. (Due to LogHandler->Router->Stream->Broker->Poller, where Stream
    # only calls start_transmit() when transitioning from empty to non-empty
    # buffer. If the start_transmit() is lost, writes from the child hang
    # permanently).
    root = logging.getLogger()
    old_level = root.level
    root.setLevel(logging.CRITICAL)

    old = broker.poller
    new = PREFERRED_POLLER()
    for fd, data in old.readers:
        new.start_receive(fd, data)
    for fd, data in old.writers:
        new.start_transmit(fd, data)

    old.close()
    broker.poller = new
    root.setLevel(old_level)
    LOG.debug('replaced %r with %r (new: %d readers, %d writers; '
              'old: %d readers, %d writers)', old, new,
              len(new.readers), len(new.writers),
              len(old.readers), len(old.writers))


@mitogen.core.takes_econtext
def upgrade_router(econtext):
    if not isinstance(econtext.router, Router):  # TODO
        econtext.broker.defer(_upgrade_broker, econtext.broker)
        econtext.router.__class__ = Router  # TODO
        econtext.router.upgrade(
            importer=econtext.importer,
            parent=econtext.parent,
        )


def stream_by_method_name(name):
    """
    Given the name of a Mitogen connection method, import its implementation
    module and return its Stream subclass.
    """
    if name == u'local':
        name = u'parent'
    module = mitogen.core.import_module(u'mitogen.' + name)
    return module.Stream


@mitogen.core.takes_econtext
def _proxy_connect(name, method_name, kwargs, econtext):
    upgrade_router(econtext)
    try:
        context = econtext.router._connect(
            klass=stream_by_method_name(method_name),
            name=name,
            **kwargs
        )
    except mitogen.core.StreamError:
        return {
            u'id': None,
            u'name': None,
            u'msg': 'error occurred on host %s: %s' % (
                socket.gethostname(),
                sys.exc_info()[1],
            ),
        }

    return {
        u'id': context.context_id,
        u'name': context.name,
        u'msg': None,
    }


def wstatus_to_str(status):
    """
    Parse and format a :func:`os.waitpid` exit status.
    """
    if os.WIFEXITED(status):
        return 'exited with return code %d' % (os.WEXITSTATUS(status),)
    if os.WIFSIGNALED(status):
        n = os.WTERMSIG(status)
        return 'exited due to signal %d (%s)' % (n, SIGNAL_BY_NUM.get(n))
    if os.WIFSTOPPED(status):
        n = os.WSTOPSIG(status)
        return 'stopped due to signal %d (%s)' % (n, SIGNAL_BY_NUM.get(n))
    return 'unknown wait status (%d)' % (status,)


class EofError(mitogen.core.StreamError):
    """
    Raised by :func:`iter_read` and :func:`write_all` when EOF is detected by
    the child process.
    """
    # inherits from StreamError to maintain compatibility.


class Argv(object):
    """
    Wrapper to defer argv formatting when debug logging is disabled.
    """
    def __init__(self, argv):
        self.argv = argv

    must_escape = frozenset('\\$"`!')
    must_escape_or_space = must_escape | frozenset(' ')

    def escape(self, x):
        if not self.must_escape_or_space.intersection(x):
            return x

        s = '"'
        for c in x:
            if c in self.must_escape:
                s += '\\'
            s += c
        s += '"'
        return s

    def __str__(self):
        return ' '.join(map(self.escape, self.argv))


class CallSpec(object):
    """
    Wrapper to defer call argument formatting when debug logging is disabled.
    """
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def _get_name(self):
        bits = [self.func.__module__]
        if inspect.ismethod(self.func):
            bits.append(getattr(self.func.__self__, '__name__', None) or
                        getattr(type(self.func.__self__), '__name__', None))
        bits.append(self.func.__name__)
        return u'.'.join(bits)

    def _get_args(self):
        return u', '.join(repr(a) for a in self.args)

    def _get_kwargs(self):
        s = u''
        if self.kwargs:
            s = u', '.join('%s=%r' % (k, v) for k, v in self.kwargs.items())
            if self.args:
                s = u', ' + s
        return s

    def __repr__(self):
        return '%s(%s%s)' % (
            self._get_name(),
            self._get_args(),
            self._get_kwargs(),
        )


class KqueuePoller(mitogen.core.Poller):
    _repr = 'KqueuePoller()'

    def __init__(self):
        self._kqueue = select.kqueue()
        self._rfds = {}
        self._wfds = {}
        self._changelist = []

    def close(self):
        self._kqueue.close()

    def _control(self, fd, filters, flags):
        mitogen.core._vv and IOLOG.debug(
            '%r._control(%r, %r, %r)', self, fd, filters, flags)
        # TODO: at shutdown it is currently possible for KQ_EV_ADD/KQ_EV_DEL
        # pairs to be pending after the associated file descriptor has already
        # been closed. Fixing this requires maintaining extra state, or perhaps
        # making fd closure the poller's responsibility. In the meantime,
        # simply apply changes immediately.
        # self._changelist.append(select.kevent(fd, filters, flags))
        changelist = [select.kevent(fd, filters, flags)]
        events, _ = mitogen.core.io_op(self._kqueue.control, changelist, 0, 0)
        assert not events

    def start_receive(self, fd, data=None):
        mitogen.core._vv and IOLOG.debug('%r.start_receive(%r, %r)',
            self, fd, data)
        if fd not in self._rfds:
            self._control(fd, select.KQ_FILTER_READ, select.KQ_EV_ADD)
        self._rfds[fd] = (data or fd, self._generation)

    def stop_receive(self, fd):
        mitogen.core._vv and IOLOG.debug('%r.stop_receive(%r)', self, fd)
        if fd in self._rfds:
            self._control(fd, select.KQ_FILTER_READ, select.KQ_EV_DELETE)
            del self._rfds[fd]

    def start_transmit(self, fd, data=None):
        mitogen.core._vv and IOLOG.debug('%r.start_transmit(%r, %r)',
            self, fd, data)
        if fd not in self._wfds:
            self._control(fd, select.KQ_FILTER_WRITE, select.KQ_EV_ADD)
        self._wfds[fd] = (data or fd, self._generation)

    def stop_transmit(self, fd):
        mitogen.core._vv and IOLOG.debug('%r.stop_transmit(%r)', self, fd)
        if fd in self._wfds:
            self._control(fd, select.KQ_FILTER_WRITE, select.KQ_EV_DELETE)
            del self._wfds[fd]

    def _poll(self, timeout):
        changelist = self._changelist
        self._changelist = []
        events, _ = mitogen.core.io_op(self._kqueue.control,
            changelist, 32, timeout)
        for event in events:
            fd = event.ident
            if event.flags & select.KQ_EV_ERROR:
                LOG.debug('ignoring stale event for fd %r: errno=%d: %s',
                          fd, event.data, errno.errorcode.get(event.data))
            elif event.filter == select.KQ_FILTER_READ:
                data, gen = self._rfds.get(fd, (None, None))
                # Events can still be read for an already-discarded fd.
                if gen and gen < self._generation:
                    mitogen.core._vv and IOLOG.debug('%r: POLLIN: %r', self, fd)
                    yield data
            elif event.filter == select.KQ_FILTER_WRITE and fd in self._wfds:
                data, gen = self._wfds.get(fd, (None, None))
                if gen and gen < self._generation:
                    mitogen.core._vv and IOLOG.debug('%r: POLLOUT: %r', self, fd)
                    yield data


class EpollPoller(mitogen.core.Poller):
    _repr = 'EpollPoller()'

    def __init__(self):
        self._epoll = select.epoll(32)
        self._registered_fds = set()
        self._rfds = {}
        self._wfds = {}

    def close(self):
        self._epoll.close()

    def _control(self, fd):
        mitogen.core._vv and IOLOG.debug('%r._control(%r)', self, fd)
        mask = (((fd in self._rfds) and select.EPOLLIN) |
                ((fd in self._wfds) and select.EPOLLOUT))
        if mask:
            if fd in self._registered_fds:
                self._epoll.modify(fd, mask)
            else:
                self._epoll.register(fd, mask)
                self._registered_fds.add(fd)
        elif fd in self._registered_fds:
            self._epoll.unregister(fd)
            self._registered_fds.remove(fd)

    def start_receive(self, fd, data=None):
        mitogen.core._vv and IOLOG.debug('%r.start_receive(%r, %r)',
            self, fd, data)
        self._rfds[fd] = (data or fd, self._generation)
        self._control(fd)

    def stop_receive(self, fd):
        mitogen.core._vv and IOLOG.debug('%r.stop_receive(%r)', self, fd)
        self._rfds.pop(fd, None)
        self._control(fd)

    def start_transmit(self, fd, data=None):
        mitogen.core._vv and IOLOG.debug('%r.start_transmit(%r, %r)',
            self, fd, data)
        self._wfds[fd] = (data or fd, self._generation)
        self._control(fd)

    def stop_transmit(self, fd):
        mitogen.core._vv and IOLOG.debug('%r.stop_transmit(%r)', self, fd)
        self._wfds.pop(fd, None)
        self._control(fd)

    _inmask = (getattr(select, 'EPOLLIN', 0) |
               getattr(select, 'EPOLLHUP', 0))

    def _poll(self, timeout):
        the_timeout = -1
        if timeout is not None:
            the_timeout = timeout

        events, _ = mitogen.core.io_op(self._epoll.poll, the_timeout, 32)
        for fd, event in events:
            if event & self._inmask:
                data, gen = self._rfds.get(fd, (None, None))
                if gen and gen < self._generation:
                    # Events can still be read for an already-discarded fd.
                    mitogen.core._vv and IOLOG.debug('%r: POLLIN: %r', self, fd)
                    yield data
            if event & select.EPOLLOUT:
                data, gen = self._wfds.get(fd, (None, None))
                if gen and gen < self._generation:
                    mitogen.core._vv and IOLOG.debug('%r: POLLOUT: %r', self, fd)
                    yield data


POLLER_BY_SYSNAME = {
    'Darwin': KqueuePoller,
    'FreeBSD': KqueuePoller,
    'Linux': EpollPoller,
}

PREFERRED_POLLER = POLLER_BY_SYSNAME.get(
    os.uname()[0],
    mitogen.core.Poller,
)

# For apps that start threads dynamically, it's possible Latch will also get
# very high-numbered wait fds when there are many connections, and so select()
# becomes useless there too. So swap in our favourite poller.
mitogen.core.Latch.poller_class = PREFERRED_POLLER


class DiagLogStream(mitogen.core.BasicStream):
    """
    For "hybrid TTY/socketpair" mode, after a connection has been setup, a
    spare TTY file descriptor will exist that cannot be closed, and to which
    SSH or sudo may continue writing log messages.

    The descriptor cannot be closed since the UNIX TTY layer will send a
    termination signal to any processes whose controlling TTY is the TTY that
    has been closed.

    DiagLogStream takes over this descriptor and creates corresponding log
    messages for anything written to it.
    """

    def __init__(self, fd, stream):
        self.receive_side = mitogen.core.Side(self, fd)
        self.transmit_side = self.receive_side
        self.stream = stream
        self.buf = ''

    def __repr__(self):
        return 'mitogen.parent.DiagLogStream(fd=%r, %r)' % (
            self.receive_side.fd,
            self.stream.name,
        )

    def on_receive(self, broker):
        """
        This handler is only called after the stream is registered with the IO
        loop, the descriptor is manually read/written by _connect_bootstrap()
        prior to that.
        """
        buf = self.receive_side.read()
        if not buf:
            return self.on_disconnect(broker)

        self.buf += buf.decode('utf-8', 'replace')
        while '\n' in self.buf:
            lines = self.buf.split('\n')
            self.buf = lines[-1]
            for line in lines[:-1]:
                LOG.debug('%r:  %r', self, line.rstrip())


class Stream(mitogen.core.Stream):
    """
    Base for streams capable of starting new slaves.
    """
    #: The path to the remote Python interpreter.
    python_path = get_sys_executable()

    #: Maximum time to wait for a connection attempt.
    connect_timeout = 30.0

    #: Derived from :py:attr:`connect_timeout`; absolute floating point
    #: UNIX timestamp after which the connection attempt should be abandoned.
    connect_deadline = None

    #: True to cause context to write verbose /tmp/mitogen.<pid>.log.
    debug = False

    #: True to cause context to write /tmp/mitogen.stats.<pid>.<thread>.log.
    profiling = False

    #: Set to the child's PID by connect().
    pid = None

    #: Passed via Router wrapper methods, must eventually be passed to
    #: ExternalContext.main().
    max_message_size = None

    def __init__(self, *args, **kwargs):
        super(Stream, self).__init__(*args, **kwargs)
        self.sent_modules = set(['mitogen', 'mitogen.core'])

    def construct(self, max_message_size, remote_name=None, python_path=None,
                  debug=False, connect_timeout=None, profiling=False,
                  unidirectional=False, old_router=None, **kwargs):
        """Get the named context running on the local machine, creating it if
        it does not exist."""
        super(Stream, self).construct(**kwargs)
        self.max_message_size = max_message_size
        if python_path:
            self.python_path = python_path
        if connect_timeout:
            self.connect_timeout = connect_timeout
        if remote_name is None:
            remote_name = get_default_remote_name()
        if '/' in remote_name or '\\' in remote_name:
            raise ValueError('remote_name= cannot contain slashes')
        self.remote_name = remote_name
        self.debug = debug
        self.profiling = profiling
        self.unidirectional = unidirectional
        self.max_message_size = max_message_size
        self.connect_deadline = time.time() + self.connect_timeout

    def on_shutdown(self, broker):
        """Request the slave gracefully shut itself down."""
        LOG.debug('%r closing CALL_FUNCTION channel', self)
        self._send(
            mitogen.core.Message(
                src_id=mitogen.context_id,
                dst_id=self.remote_id,
                handle=mitogen.core.SHUTDOWN,
            )
        )

    #: If :data:`True`, indicates the subprocess managed by us should not be
    #: killed during graceful detachment, as it the actual process implementing
    #: the child context. In all other cases, the subprocess is SSH, sudo, or a
    #: similar tool that should be reminded to quit during disconnection.
    child_is_immediate_subprocess = True

    detached = False
    _reaped = False

    def _reap_child(self):
        """
        Reap the child process during disconnection.
        """
        if self.detached and self.child_is_immediate_subprocess:
            LOG.debug('%r: immediate child is detached, won\'t reap it', self)
            return

        if self._reaped:
            # on_disconnect() may be invoked more than once, for example, if
            # there is still a pending message to be sent after the first
            # on_disconnect() call.
            return

        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
        except OSError:
            e = sys.exc_info()[1]
            if e.args[0] == errno.ECHILD:
                LOG.warn('%r: waitpid(%r) produced ECHILD', self, self.pid)
                return
            raise

        self._reaped = True
        if pid:
            LOG.debug('%r: PID %d %s', self, pid, wstatus_to_str(status))
            return

        # For processes like sudo we cannot actually send sudo a signal,
        # because it is setuid, so this is best-effort only.
        LOG.debug('%r: child process still alive, sending SIGTERM', self)
        try:
            os.kill(self.pid, signal.SIGTERM)
        except OSError:
            e = sys.exc_info()[1]
            if e.args[0] != errno.EPERM:
                raise

    def on_disconnect(self, broker):
        self._reap_child()
        super(Stream, self).on_disconnect(broker)

    # Minimised, gzipped, base64'd and passed to 'python -c'. It forks, dups
    # file descriptor 0 as 100, creates a pipe, then execs a new interpreter
    # with a custom argv.
    #   * Optimized for minimum byte count after minification & compression.
    #   * 'CONTEXT_NAME' and 'PREAMBLE_COMPRESSED_LEN' are substituted with
    #     their respective values.
    #   * CONTEXT_NAME must be prefixed with the name of the Python binary in
    #     order to allow virtualenvs to detect their install prefix.
    #   * For Darwin, OS X installs a craptacular argv0-introspecting Python
    #     version switcher as /usr/bin/python. Override attempts to call it
    #     with an explicit call to python2.7
    #
    # Locals:
    #   R: read side of interpreter stdin.
    #   W: write side of interpreter stdin.
    #   r: read side of core_src FD.
    #   w: write side of core_src FD.
    #   C: the decompressed core source.
    @staticmethod
    def _first_stage():
        R,W=os.pipe()
        r,w=os.pipe()
        if os.fork():
            os.dup2(0,100)
            os.dup2(R,0)
            os.dup2(r,101)
            os.close(R)
            os.close(r)
            os.close(W)
            os.close(w)
            if sys.platform == 'darwin' and sys.executable == '/usr/bin/python':
                sys.executable += sys.version[:3]
            os.environ['ARGV0']=sys.executable
            os.execl(sys.executable,sys.executable+'(mitogen:CONTEXT_NAME)')
        os.write(1,'MITO000\n'.encode())
        C=_(os.fdopen(0,'rb').read(PREAMBLE_COMPRESSED_LEN),'zip')
        fp=os.fdopen(W,'wb',0)
        fp.write(C)
        fp.close()
        fp=os.fdopen(w,'wb',0)
        fp.write(C)
        fp.close()
        os.write(1,'MITO001\n'.encode())

    def get_python_argv(self):
        """
        Return the initial argument vector elements necessary to invoke Python,
        by returning a 1-element list containing :attr:`python_path` if it is a
        string, or simply returning it if it is already a list.

        This allows emulation of existing tools where the Python invocation may
        be set to e.g. `['/usr/bin/env', 'python']`.
        """
        if isinstance(self.python_path, list):
            return self.python_path
        return [self.python_path]

    def get_boot_command(self):
        source = inspect.getsource(self._first_stage)
        source = textwrap.dedent('\n'.join(source.strip().split('\n')[2:]))
        source = source.replace('    ', '\t')
        source = source.replace('CONTEXT_NAME', self.remote_name)
        preamble_compressed = self.get_preamble()
        source = source.replace('PREAMBLE_COMPRESSED_LEN',
                                str(len(preamble_compressed)))
        compressed = zlib.compress(source.encode(), 9)
        encoded = codecs.encode(compressed, 'base64').replace(b('\n'), b(''))
        # We can't use bytes.decode() in 3.x since it was restricted to always
        # return unicode, so codecs.decode() is used instead. In 3.x
        # codecs.decode() requires a bytes object. Since we must be compatible
        # with 2.4 (no bytes literal), an extra .encode() either returns the
        # same str (2.x) or an equivalent bytes (3.x).
        return self.get_python_argv() + [
            '-c',
            'import codecs,os,sys;_=codecs.decode;'
            'exec(_(_("%s".encode(),"base64"),"zip"))' % (encoded.decode(),)
        ]

    def get_econtext_config(self):
        assert self.max_message_size is not None
        parent_ids = mitogen.parent_ids[:]
        parent_ids.insert(0, mitogen.context_id)
        return {
            'parent_ids': parent_ids,
            'context_id': self.remote_id,
            'debug': self.debug,
            'profiling': self.profiling,
            'unidirectional': self.unidirectional,
            'log_level': get_log_level(),
            'whitelist': self._router.get_module_whitelist(),
            'blacklist': self._router.get_module_blacklist(),
            'max_message_size': self.max_message_size,
            'version': mitogen.__version__,
        }

    def get_preamble(self):
        source = get_core_source()
        source += '\nExternalContext(%r).main()\n' % (
            self.get_econtext_config(),
        )
        return zlib.compress(source.encode('utf-8'), 9)

    create_child = staticmethod(create_child)
    create_child_args = {}
    name_prefix = u'local'

    def start_child(self):
        args = self.get_boot_command()
        try:
            return self.create_child(args, **self.create_child_args)
        except OSError:
            e = sys.exc_info()[1]
            msg = 'Child start failed: %s. Command was: %s' % (e, Argv(args))
            raise mitogen.core.StreamError(msg)

    eof_error_hint = None

    def _adorn_eof_error(self, e):
        """
        Used by subclasses to provide additional information in the case of a
        failed connection.
        """
        if self.eof_error_hint:
            e.args = ('%s\n\n%s' % (e.args[0], self.eof_error_hint),)

    def connect(self):
        LOG.debug('%r.connect()', self)
        self.pid, fd, extra_fd = self.start_child()
        self.name = u'%s.%s' % (self.name_prefix, self.pid)
        self.receive_side = mitogen.core.Side(self, fd)
        self.transmit_side = mitogen.core.Side(self, os.dup(fd))
        LOG.debug('%r.connect(): child process stdin/stdout=%r',
                  self, self.receive_side.fd)

        try:
            self._connect_bootstrap(extra_fd)
        except EofError:
            e = sys.exc_info()[1]
            self._adorn_eof_error(e)
            raise
        except Exception:
            self._reap_child()
            raise

    #: Sentinel value emitted by the first stage to indicate it is ready to
    #: receive the compressed bootstrap. For :mod:`mitogen.ssh` this must have
    #: length of at least `max(len('password'), len('debug1:'))`
    EC0_MARKER = mitogen.core.b('MITO000\n')
    EC1_MARKER = mitogen.core.b('MITO001\n')

    def _ec0_received(self):
        LOG.debug('%r._ec0_received()', self)
        write_all(self.transmit_side.fd, self.get_preamble())
        discard_until(self.receive_side.fd, self.EC1_MARKER,
                      self.connect_deadline)

    def _connect_bootstrap(self, extra_fd):
        discard_until(self.receive_side.fd, self.EC0_MARKER,
                      self.connect_deadline)
        self._ec0_received()


class ChildIdAllocator(object):
    def __init__(self, router):
        self.router = router
        self.lock = threading.Lock()
        self.it = iter(xrange(0))

    def allocate(self):
        self.lock.acquire()
        try:
            for id_ in self.it:
                return id_

            master = mitogen.core.Context(self.router, 0)
            start, end = master.send_await(
                mitogen.core.Message(dst_id=0, handle=mitogen.core.ALLOCATE_ID)
            )
            self.it = iter(xrange(start, end))
        finally:
            self.lock.release()

        return self.allocate()


class CallChain(object):
    """
    Deliver :data:`mitogen.core.CALL_FUNCTION` messages to a target context,
    optionally threading related calls so an exception in an earlier call
    cancels subsequent calls.

    :param mitogen.core.Context context:
        Target context.
    :param bool pipelined:
        Enable pipelining.

    :meth:`call`, :meth:`call_no_reply` and :meth:`call_async`
    normally issue calls and produce responses with no memory of prior
    exceptions. If a call made with :meth:`call_no_reply` fails, the exception
    is logged to the target context's logging framework.

    **Pipelining**

    When pipelining is enabled, if an exception occurs during a call,
    subsequent calls made by the same :class:`CallChain` fail with the same
    exception, including those already in-flight on the network, and no further
    calls execute until :meth:`reset` is invoked.

    No exception is logged for calls made with :meth:`call_no_reply`, instead
    the exception is saved and reported as the result of subsequent
    :meth:`call` or :meth:`call_async` calls.

    Sequences of asynchronous calls can be made without wasting network
    round-trips to discover if prior calls succeed, and chains originating from
    multiple unrelated source contexts may overlap concurrently at a target
    context without interference.

    In this example, 4 calls complete in one round-trip::

        chain = mitogen.parent.CallChain(context, pipelined=True)
        chain.call_no_reply(os.mkdir, '/tmp/foo')

        # If previous mkdir() failed, this never runs:
        chain.call_no_reply(os.mkdir, '/tmp/foo/bar')

        # If either mkdir() failed, this never runs, and the exception is
        # asynchronously delivered to the receiver.
        recv = chain.call_async(subprocess.check_output, '/tmp/foo')

        # If anything so far failed, this never runs, and raises the exception.
        chain.call(do_something)

        # If this code was executed, the exception would also be raised.
        if recv.get().unpickle() == 'baz':
            pass

    When pipelining is enabled, :meth:`reset` must be invoked to ensure any
    exception is discarded, otherwise unbounded memory usage is possible in
    long-running programs. The context manager protocol is supported to ensure
    :meth:`reset` is always invoked::

        with mitogen.parent.CallChain(context, pipelined=True) as chain:
            chain.call_no_reply(...)
            chain.call_no_reply(...)
            chain.call_no_reply(...)
            chain.call(...)

        # chain.reset() automatically invoked.
    """
    def __init__(self, context, pipelined=False):
        self.context = context
        if pipelined:
            self.chain_id = self.make_chain_id()
        else:
            self.chain_id = None

    @classmethod
    def make_chain_id(cls):
        return '%s-%s-%x-%x' % (
            socket.gethostname(),
            os.getpid(),
            threading.currentThread().ident,
            int(1e6 * time.time()),
        )

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.context)

    def __enter__(self):
        return self

    def __exit__(self, _1, _2, _3):
        self.reset()

    def reset(self):
        """
        Instruct the target to forget any related exception.
        """
        if not self.chain_id:
            return

        saved, self.chain_id = self.chain_id, None
        try:
            self.call_no_reply(mitogen.core.Dispatcher.forget_chain, saved)
        finally:
            self.chain_id = saved

    def make_msg(self, fn, *args, **kwargs):
        if inspect.ismethod(fn) and inspect.isclass(fn.__self__):
            klass = mitogen.core.to_text(fn.__self__.__name__)
        else:
            klass = None

        tup = (
            self.chain_id,
            mitogen.core.to_text(fn.__module__),
            klass,
            mitogen.core.to_text(fn.__name__),
            args,
            mitogen.core.Kwargs(kwargs)
        )
        return mitogen.core.Message.pickled(tup,
            handle=mitogen.core.CALL_FUNCTION)

    def call_no_reply(self, fn, *args, **kwargs):
        """
        Like :meth:`call_async`, but do not wait for a return value, and inform
        the target context no reply is expected. If the call fails and
        pipelining is disabled, the exception will be logged to the target
        context's logging framework.
        """
        LOG.debug('%r.call_no_reply(): %r', self, CallSpec(fn, args, kwargs))
        self.context.send(self.make_msg(fn, *args, **kwargs))

    def call_async(self, fn, *args, **kwargs):
        """
        Arrange for `fn(*args, **kwargs)` to be invoked on the context's main
        thread.

        :param fn:
            A free function in module scope or a class method of a class
            directly reachable from module scope:

            .. code-block:: python

                # mymodule.py

                def my_func():
                    '''A free function reachable as mymodule.my_func'''

                class MyClass:
                    @classmethod
                    def my_classmethod(cls):
                        '''Reachable as mymodule.MyClass.my_classmethod'''

                    def my_instancemethod(self):
                        '''Unreachable: requires a class instance!'''

                    class MyEmbeddedClass:
                        @classmethod
                        def my_classmethod(cls):
                            '''Not directly reachable from module scope!'''

        :param tuple args:
            Function arguments, if any. See :ref:`serialization-rules` for
            permitted types.
        :param dict kwargs:
            Function keyword arguments, if any. See :ref:`serialization-rules`
            for permitted types.
        :returns:
            :class:`mitogen.core.Receiver` configured to receive the result of
            the invocation:

            .. code-block:: python

                recv = context.call_async(os.check_output, 'ls /tmp/')
                try:
                    # Prints output once it is received.
                    msg = recv.get()
                    print(msg.unpickle())
                except mitogen.core.CallError, e:
                    print('Call failed:', str(e))

            Asynchronous calls may be dispatched in parallel to multiple
            contexts and consumed as they complete using
            :class:`mitogen.select.Select`.
        """
        LOG.debug('%r.call_async(): %r', self, CallSpec(fn, args, kwargs))
        return self.context.send_async(self.make_msg(fn, *args, **kwargs))

    def call(self, fn, *args, **kwargs):
        """
        Like :meth:`call_async`, but block until the return value is available.
        Equivalent to::

            call_async(fn, *args, **kwargs).get().unpickle()

        :returns:
            The function's return value.
        :raises mitogen.core.CallError:
            An exception was raised in the remote context during execution.
        """
        receiver = self.call_async(fn, *args, **kwargs)
        return receiver.get().unpickle(throw_dead=False)


class Context(mitogen.core.Context):
    call_chain_class = CallChain
    via = None

    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        self.default_call_chain = self.call_chain_class(self)

    def __eq__(self, other):
        return (isinstance(other, mitogen.core.Context) and
                (other.context_id == self.context_id) and
                (other.router == self.router))

    def __hash__(self):
        return hash((self.router, self.context_id))

    def call_async(self, fn, *args, **kwargs):
        return self.default_call_chain.call_async(fn, *args, **kwargs)

    def call(self, fn, *args, **kwargs):
        return self.default_call_chain.call(fn, *args, **kwargs)

    def call_no_reply(self, fn, *args, **kwargs):
        self.default_call_chain.call_no_reply(fn, *args, **kwargs)

    def shutdown(self, wait=False):
        LOG.debug('%r.shutdown() sending SHUTDOWN', self)
        latch = mitogen.core.Latch()
        mitogen.core.listen(self, 'disconnect', lambda: latch.put(None))
        self.send(
            mitogen.core.Message(
                handle=mitogen.core.SHUTDOWN,
            )
        )

        if wait:
            latch.get()
        else:
            return latch


class RouteMonitor(object):
    def __init__(self, router, parent=None):
        self.router = router
        self.parent = parent
        self.router.add_handler(
            fn=self._on_add_route,
            handle=mitogen.core.ADD_ROUTE,
            persist=True,
            policy=is_immediate_child,
        )
        self.router.add_handler(
            fn=self._on_del_route,
            handle=mitogen.core.DEL_ROUTE,
            persist=True,
            policy=is_immediate_child,
        )
        #: Mapping of Stream instance to integer context IDs reachable via the
        #: stream; used to cleanup routes during disconnection.
        self._routes_by_stream = {}

    def _send_one(self, stream, handle, target_id, name):
        data = str(target_id)
        if name:
            data = '%s:%s' % (target_id, mitogen.core.b(name))
        stream.send(
            mitogen.core.Message(
                handle=handle,
                data=data.encode('utf-8'),
                dst_id=stream.remote_id,
            )
        )

    def _propagate(self, handle, target_id, name=None):
        if not self.parent:
            # self.parent is None in the master.
            return

        stream = self.router.stream_by_id(self.parent.context_id)
        self._send_one(stream, handle, target_id, name)

    def _child_propagate(self, handle, target_id):
        """
        For DEL_ROUTE, we additionally want to broadcast the message to any
        stream that has ever communicated with the disconnecting ID, so
        core.py's :meth:`mitogen.core.Router._on_del_route` can turn the
        message into a disconnect event.
        """
        for stream in itervalues(self.router._stream_by_id):
            if target_id in stream.egress_ids:
                self._send_one(stream, mitogen.core.DEL_ROUTE, target_id, None)

    def notice_stream(self, stream):
        """
        When this parent is responsible for a new directly connected child
        stream, we're also responsible for broadcasting DEL_ROUTE upstream
        if/when that child disconnects.
        """
        self._routes_by_stream[stream] = set([stream.remote_id])
        self._propagate(mitogen.core.ADD_ROUTE, stream.remote_id,
                        stream.name)
        mitogen.core.listen(
            obj=stream,
            name='disconnect',
            func=lambda: self._on_stream_disconnect(stream),
        )

    def get_routes(self, stream):
        """
        Return the set of context IDs reachable on a stream.

        :param mitogen.core.Stream stream:
        :returns: set([int])
        """
        return self._routes_by_stream.get(stream) or set()

    def _on_stream_disconnect(self, stream):
        """
        Respond to disconnection of a local stream by
        """
        routes = self._routes_by_stream.pop(stream)
        LOG.debug('%r is gone; propagating DEL_ROUTE for %r', stream, routes)
        for target_id in routes:
            self.router.del_route(target_id)
            self._propagate(mitogen.core.DEL_ROUTE, target_id)
            self._child_propagate(mitogen.core.DEL_ROUTE, target_id)

            context = self.router.context_by_id(target_id, create=False)
            if context:
                mitogen.core.fire(context, 'disconnect')

    def _on_add_route(self, msg):
        if msg.is_dead:
            return

        target_id_s, _, target_name = msg.data.partition(b(':'))
        target_name = target_name.decode()
        target_id = int(target_id_s)
        self.router.context_by_id(target_id).name = target_name
        stream = self.router.stream_by_id(msg.auth_id)
        current = self.router.stream_by_id(target_id)
        if current and current.remote_id != mitogen.parent_id:
            LOG.error('Cannot add duplicate route to %r via %r, '
                      'already have existing route via %r',
                      target_id, stream, current)
            return

        LOG.debug('Adding route to %d via %r', target_id, stream)
        self._routes_by_stream[stream].add(target_id)
        self.router.add_route(target_id, stream)
        self._propagate(mitogen.core.ADD_ROUTE, target_id, target_name)

    def _on_del_route(self, msg):
        if msg.is_dead:
            return

        target_id = int(msg.data)
        registered_stream = self.router.stream_by_id(target_id)
        stream = self.router.stream_by_id(msg.auth_id)
        if registered_stream != stream:
            LOG.error('Received DEL_ROUTE for %d from %r, expected %r',
                      target_id, stream, registered_stream)
            return

        context = self.router.context_by_id(target_id, create=False)
        if context:
            LOG.debug('%r: Firing local disconnect for %r', self, context)
            mitogen.core.fire(context, 'disconnect')

        LOG.debug('Deleting route to %d via %r', target_id, stream)
        routes = self._routes_by_stream.get(stream)
        if routes:
            routes.discard(target_id)

        self.router.del_route(target_id)
        if stream.remote_id != mitogen.parent_id:
            self._propagate(mitogen.core.DEL_ROUTE, target_id)
        self._child_propagate(mitogen.core.DEL_ROUTE, target_id)


class Router(mitogen.core.Router):
    context_class = Context
    debug = False
    profiling = False

    id_allocator = None
    responder = None
    log_forwarder = None
    route_monitor = None

    def upgrade(self, importer, parent):
        LOG.debug('%r.upgrade()', self)
        self.id_allocator = ChildIdAllocator(router=self)
        self.responder = ModuleForwarder(
            router=self,
            parent_context=parent,
            importer=importer,
        )
        self.route_monitor = RouteMonitor(self, parent)
        self.add_handler(
            fn=self._on_detaching,
            handle=mitogen.core.DETACHING,
            persist=True,
        )

    def _on_detaching(self, msg):
        if msg.is_dead:
            return
        stream = self.stream_by_id(msg.src_id)
        if stream.remote_id != msg.src_id or stream.detached:
            LOG.warning('bad DETACHING received on %r: %r', stream, msg)
            return
        LOG.debug('%r: marking as detached', stream)
        stream.detached = True
        msg.reply(None)

    def add_route(self, target_id, stream):
        LOG.debug('%r.add_route(%r, %r)', self, target_id, stream)
        assert isinstance(target_id, int)
        assert isinstance(stream, Stream)
        try:
            self._stream_by_id[target_id] = stream
        except KeyError:
            LOG.error('%r: cant add route to %r via %r: no such stream',
                      self, target_id, stream)

    def del_route(self, target_id):
        LOG.debug('%r.del_route(%r)', self, target_id)
        # DEL_ROUTE may be sent by a parent if it knows this context sent
        # messages to a peer that has now disconnected, to let us raise
        # 'disconnect' event on the appropriate Context instance. In that case,
        # we won't a matching _stream_by_id entry for the disappearing route,
        # so don't raise an error for a missing key here.
        self._stream_by_id.pop(target_id, None)

    def get_module_blacklist(self):
        if mitogen.context_id == 0:
            return self.responder.blacklist
        return self.importer.blacklist

    def get_module_whitelist(self):
        if mitogen.context_id == 0:
            return self.responder.whitelist
        return self.importer.whitelist

    def allocate_id(self):
        return self.id_allocator.allocate()

    connection_timeout_msg = u"Connection timed out."

    def _connect(self, klass, name=None, **kwargs):
        context_id = self.allocate_id()
        context = self.context_class(self, context_id)
        kwargs['old_router'] = self
        kwargs['max_message_size'] = self.max_message_size
        stream = klass(self, context_id, **kwargs)
        if name is not None:
            stream.name = name
        try:
            stream.connect()
        except mitogen.core.TimeoutError:
            raise mitogen.core.StreamError(self.connection_timeout_msg)
        context.name = stream.name
        self.route_monitor.notice_stream(stream)
        self.register(context, stream)
        return context

    def connect(self, method_name, name=None, **kwargs):
        klass = stream_by_method_name(method_name)
        kwargs.setdefault(u'debug', self.debug)
        kwargs.setdefault(u'profiling', self.profiling)
        kwargs.setdefault(u'unidirectional', self.unidirectional)

        via = kwargs.pop(u'via', None)
        if via is not None:
            return self.proxy_connect(via, method_name, name=name, **kwargs)
        return self._connect(klass, name=name, **kwargs)

    def proxy_connect(self, via_context, method_name, name=None, **kwargs):
        resp = via_context.call(_proxy_connect,
            name=name,
            method_name=method_name,
            kwargs=mitogen.core.Kwargs(kwargs),
        )
        if resp['msg'] is not None:
            raise mitogen.core.StreamError(resp['msg'])

        name = u'%s.%s' % (via_context.name, resp['name'])
        context = self.context_class(self, resp['id'], name=name)
        context.via = via_context
        self._context_by_id[context.context_id] = context
        return context

    def doas(self, **kwargs):
        return self.connect(u'doas', **kwargs)

    def docker(self, **kwargs):
        return self.connect(u'docker', **kwargs)

    def kubectl(self, **kwargs):
        return self.connect(u'kubectl', **kwargs)

    def fork(self, **kwargs):
        return self.connect(u'fork', **kwargs)

    def jail(self, **kwargs):
        return self.connect(u'jail', **kwargs)

    def local(self, **kwargs):
        return self.connect(u'local', **kwargs)

    def lxc(self, **kwargs):
        return self.connect(u'lxc', **kwargs)

    def lxd(self, **kwargs):
        return self.connect(u'lxd', **kwargs)

    def setns(self, **kwargs):
        return self.connect(u'setns', **kwargs)

    def su(self, **kwargs):
        return self.connect(u'su', **kwargs)

    def sudo(self, **kwargs):
        return self.connect(u'sudo', **kwargs)

    def ssh(self, **kwargs):
        return self.connect(u'ssh', **kwargs)


class ProcessMonitor(object):
    def __init__(self):
        # pid -> callback()
        self.callback_by_pid = {}
        signal.signal(signal.SIGCHLD, self._on_sigchld)

    def _on_sigchld(self, _signum, _frame):
        for pid, callback in self.callback_by_pid.items():
            pid, status = os.waitpid(pid, os.WNOHANG)
            if pid:
                callback(status)
                del self.callback_by_pid[pid]

    def add(self, pid, callback):
        self.callback_by_pid[pid] = callback

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class ModuleForwarder(object):
    """
    Respond to GET_MODULE requests in a slave by forwarding the request to our
    parent context, or satisfying the request from our local Importer cache.
    """
    def __init__(self, router, parent_context, importer):
        self.router = router
        self.parent_context = parent_context
        self.importer = importer
        router.add_handler(
            fn=self._on_forward_module,
            handle=mitogen.core.FORWARD_MODULE,
            persist=True,
            policy=mitogen.core.has_parent_authority,
        )
        router.add_handler(
            fn=self._on_get_module,
            handle=mitogen.core.GET_MODULE,
            persist=True,
            policy=is_immediate_child,
        )

    def __repr__(self):
        return 'ModuleForwarder(%r)' % (self.router,)

    def _on_forward_module(self, msg):
        if msg.is_dead:
            return

        context_id_s, _, fullname = msg.data.partition(b('\x00'))
        fullname = mitogen.core.to_text(fullname)
        context_id = int(context_id_s)
        stream = self.router.stream_by_id(context_id)
        if stream.remote_id == mitogen.parent_id:
            LOG.error('%r: dropping FORWARD_MODULE(%d, %r): no route to child',
                      self, context_id, fullname)
            return

        if fullname in stream.sent_modules:
            return

        LOG.debug('%r._on_forward_module() sending %r to %r via %r',
                  self, fullname, context_id, stream.remote_id)
        self._send_module_and_related(stream, fullname)
        if stream.remote_id != context_id:
            stream._send(
                mitogen.core.Message(
                    data=msg.data,
                    handle=mitogen.core.FORWARD_MODULE,
                    dst_id=stream.remote_id,
                )
            )

    def _on_get_module(self, msg):
        LOG.debug('%r._on_get_module(%r)', self, msg)
        if msg.is_dead:
            return

        fullname = msg.data.decode('utf-8')
        callback = lambda: self._on_cache_callback(msg, fullname)
        self.importer._request_module(fullname, callback)

    def _send_one_module(self, msg, tup):
        self.router._async_route(
            mitogen.core.Message.pickled(
                tup,
                dst_id=msg.src_id,
                handle=mitogen.core.LOAD_MODULE,
            )
        )

    def _on_cache_callback(self, msg, fullname):
        LOG.debug('%r._on_get_module(): sending %r', self, fullname)
        stream = self.router.stream_by_id(msg.src_id)
        self._send_module_and_related(stream, fullname)

    def _send_module_and_related(self, stream, fullname):
        tup = self.importer._cache[fullname]
        for related in tup[4]:
            rtup = self.importer._cache.get(related)
            if rtup:
                self._send_one_module(stream, rtup)
            else:
                LOG.debug('%r._send_module_and_related(%r): absent: %r',
                           self, fullname, related)

        self._send_one_module(stream, tup)

    def _send_one_module(self, stream, tup):
        if tup[0] not in stream.sent_modules:
            stream.sent_modules.add(tup[0])
            self.router._async_route(
                mitogen.core.Message.pickled(
                    tup,
                    dst_id=stream.remote_id,
                    handle=mitogen.core.LOAD_MODULE,
                )
            )
