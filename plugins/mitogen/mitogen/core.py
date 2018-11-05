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
This module implements most package functionality, but remains separate from
non-essential code in order to reduce its size, since it is also serves as the
bootstrap implementation sent to every new slave context.
"""

import collections
import encodings.latin_1
import errno
import fcntl
import imp
import itertools
import logging
import os
import signal
import socket
import struct
import sys
import threading
import time
import traceback
import warnings
import weakref
import zlib

# Absolute imports for <2.5.
select = __import__('select')

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

# TODO: usage of 'import' after setting __name__, but before fixing up
# sys.modules generates a warning. This happens when profiling = True.
warnings.filterwarnings('ignore',
    "Parent module 'mitogen' not found while handling absolute import")

LOG = logging.getLogger('mitogen')
IOLOG = logging.getLogger('mitogen.io')
IOLOG.setLevel(logging.INFO)

LATIN1_CODEC = encodings.latin_1.Codec()

_v = False
_vv = False

GET_MODULE = 100
CALL_FUNCTION = 101
FORWARD_LOG = 102
ADD_ROUTE = 103
DEL_ROUTE = 104
ALLOCATE_ID = 105
SHUTDOWN = 106
LOAD_MODULE = 107
FORWARD_MODULE = 108
DETACHING = 109
CALL_SERVICE = 110

#: Special value used to signal disconnection or the inability to route a
#: message, when it appears in the `reply_to` field. Usually causes
#: :class:`mitogen.core.ChannelError` to be raised when it is received.
#:
#: It indicates the sender did not know how to process the message, or wishes
#: no further messages to be delivered to it. It is used when:
#:
#:  * a remote receiver is disconnected or explicitly closed.
#:  * a related message could not be delivered due to no route existing for it.
#:  * a router is being torn down, as a sentinel value to notify
#:    :py:meth:`mitogen.core.Router.add_handler` callbacks to clean up.
IS_DEAD = 999

try:
    BaseException
except NameError:
    BaseException = Exception

PY3 = sys.version_info > (3,)
if PY3:
    b = str.encode
    BytesType = bytes
    UnicodeType = str
    FsPathTypes = (str,)
    BufferType = lambda buf, start: memoryview(buf)[start:]
    long = int
else:
    b = str
    BytesType = str
    FsPathTypes = (str, unicode)
    BufferType = buffer
    UnicodeType = unicode

AnyTextType = (BytesType, UnicodeType)

if sys.version_info < (2, 5):
    next = lambda it: it.next()

#: Default size for calls to :meth:`Side.read` or :meth:`Side.write`, and the
#: size of buffers configured by :func:`mitogen.parent.create_socketpair`. This
#: value has many performance implications, 128KiB seems to be a sweet spot.
#:
#: * When set low, large messages cause many :class:`Broker` IO loop
#:   iterations, burning CPU and reducing throughput.
#: * When set high, excessive RAM is reserved by the OS for socket buffers (2x
#:   per child), and an identically sized temporary userspace buffer is
#:   allocated on each read that requires zeroing, and over a particular size
#:   may require two system calls to allocate/deallocate.
#:
#: Care must be taken to ensure the underlying kernel object and receiving
#: program support the desired size. For example,
#:
#: * Most UNIXes have TTYs with fixed 2KiB-4KiB buffers, making them unsuitable
#:   for efficient IO.
#: * Different UNIXes have varying presets for pipes, which may not be
#:   configurable. On recent Linux the default pipe buffer size is 64KiB, but
#:   under memory pressure may be as low as 4KiB for unprivileged processes.
#: * When communication is via an intermediary process, its internal buffers
#:   effect the speed OS buffers will drain. For example OpenSSH uses 64KiB
#:   reads.
#:
#: An ideal :class:`Message` has a size that is a multiple of
#: :data:`CHUNK_SIZE` inclusive of headers, to avoid wasting IO loop iterations
#: writing small trailer chunks.
CHUNK_SIZE = 131072

_tls = threading.local()


if __name__ == 'mitogen.core':
    # When loaded using import mechanism, ExternalContext.main() will not have
    # a chance to set the synthetic mitogen global, so just import it here.
    import mitogen
else:
    # When loaded as __main__, ensure classes and functions gain a __module__
    # attribute consistent with the host process, so that pickling succeeds.
    __name__ = 'mitogen.core'


class Error(Exception):
    """Base for all exceptions raised by Mitogen.

    :param str fmt:
        Exception text, or format string if `args` is non-empty.
    :param tuple args:
        Format string arguments.
    """
    def __init__(self, fmt=None, *args):
        if args:
            fmt %= args
        if fmt and not isinstance(fmt, UnicodeType):
            fmt = fmt.decode('utf-8')
        Exception.__init__(self, fmt)


class LatchError(Error):
    """Raised when an attempt is made to use a :py:class:`mitogen.core.Latch`
    that has been marked closed."""
    pass


class Blob(BytesType):
    """A serializable bytes subclass whose content is summarized in repr()
    output, making it suitable for logging binary data."""
    def __repr__(self):
        return '[blob: %d bytes]' % len(self)

    def __reduce__(self):
        return (Blob, (BytesType(self),))


class Secret(UnicodeType):
    """A serializable unicode subclass whose content is masked in repr()
    output, making it suitable for logging passwords."""
    def __repr__(self):
        return '[secret]'

    if not PY3:
        # TODO: what is this needed for in 2.x?
        def __str__(self):
            return UnicodeType(self)

    def __reduce__(self):
        return (Secret, (UnicodeType(self),))


class Kwargs(dict):
    """A serializable dict subclass that indicates the contained keys should be
    be coerced to Unicode on Python 3 as required. Python 2 produces keyword
    argument dicts whose keys are bytestrings, requiring a helper to ensure
    compatibility with Python 3."""
    if PY3:
        def __init__(self, dct):
            for k, v in dct.items():
                if type(k) is bytes:
                    self[k.decode()] = v
                else:
                    self[k] = v

    def __repr__(self):
        return 'Kwargs(%s)' % (dict.__repr__(self),)

    def __reduce__(self):
        return (Kwargs, (dict(self),))


class CallError(Error):
    """Serializable :class:`Error` subclass raised when
    :py:meth:`Context.call() <mitogen.parent.Context.call>` fails. A copy of
    the traceback from the external context is appended to the exception
    message."""
    def __init__(self, fmt=None, *args):
        if not isinstance(fmt, BaseException):
            Error.__init__(self, fmt, *args)
        else:
            e = fmt
            fmt = '%s.%s: %s' % (type(e).__module__, type(e).__name__, e)
            args = ()
            tb = sys.exc_info()[2]
            if tb:
                fmt += '\n'
                fmt += ''.join(traceback.format_tb(tb))
            Error.__init__(self, fmt)

    def __reduce__(self):
        return (_unpickle_call_error, (self.args[0],))


def _unpickle_call_error(s):
    if not (type(s) is UnicodeType and len(s) < 10000):
        raise TypeError('cannot unpickle CallError: bad input')
    inst = CallError.__new__(CallError)
    Exception.__init__(inst, s)
    return inst


class ChannelError(Error):
    """Raised when a channel dies or has been closed."""
    remote_msg = 'Channel closed by remote end.'
    local_msg = 'Channel closed by local end.'


class StreamError(Error):
    """Raised when a stream cannot be established."""
    pass


class TimeoutError(Error):
    """Raised when a timeout occurs on a stream."""
    pass


def to_text(o):
    """Coerce `o` to Unicode by decoding it from UTF-8 if it is an instance of
    :class:`bytes`, otherwise pass it to the :class:`str` constructor. The
    returned object is always a plain :class:`str`, any subclass is removed."""
    if isinstance(o, BytesType):
        return o.decode('utf-8')
    return UnicodeType(o)


def has_parent_authority(msg, _stream=None):
    """Policy function for use with :class:`Receiver` and
    :meth:`Router.add_handler` that requires incoming messages to originate
    from a parent context, or on a :class:`Stream` whose :attr:`auth_id
    <Stream.auth_id>` has been set to that of a parent context or the current
    context."""
    return (msg.auth_id == mitogen.context_id or
            msg.auth_id in mitogen.parent_ids)


def listen(obj, name, func):
    """
    Arrange for `func(*args, **kwargs)` to be invoked when the named signal is
    fired by `obj`.
    """
    signals = vars(obj).setdefault('_signals', {})
    signals.setdefault(name, []).append(func)


def fire(obj, name, *args, **kwargs):
    """
    Arrange for `func(*args, **kwargs)` to be invoked for every function
    registered for the named signal on `obj`.
    """
    signals = vars(obj).get('_signals', {})
    return [func(*args, **kwargs) for func in signals.get(name, ())]


def takes_econtext(func):
    func.mitogen_takes_econtext = True
    return func


def takes_router(func):
    func.mitogen_takes_router = True
    return func


def is_blacklisted_import(importer, fullname):
    """
    Return :data:`True` if `fullname` is part of a blacklisted package, or if
    any packages have been whitelisted and `fullname` is not part of one.

    NB:
      - If a package is on both lists, then it is treated as blacklisted.
      - If any package is whitelisted, then all non-whitelisted packages are
        treated as blacklisted.
    """
    return ((not any(fullname.startswith(s) for s in importer.whitelist)) or
                (any(fullname.startswith(s) for s in importer.blacklist)))


def set_cloexec(fd):
    """Set the file descriptor `fd` to automatically close on
    :func:`os.execve`. This has no effect on file descriptors inherited across
    :func:`os.fork`, they must be explicitly closed through some other means,
    such as :func:`mitogen.fork.on_fork`."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    assert fd > 2
    fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)


def set_nonblock(fd):
    """Set the file descriptor `fd` to non-blocking mode. For most underlying
    file types, this causes :func:`os.read` or :func:`os.write` to raise
    :class:`OSError` with :data:`errno.EAGAIN` rather than block the thread
    when the underlying kernel buffer is exhausted."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def set_block(fd):
    """Inverse of :func:`set_nonblock`, i.e. cause `fd` to block the thread
    when the underlying kernel buffer is exhausted."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)


def io_op(func, *args):
    """Wrap `func(*args)` that may raise :class:`select.error`,
    :class:`IOError`, or :class:`OSError`, trapping UNIX error codes relating
    to disconnection and retry events in various subsystems:

    * When a signal is delivered to the process on Python 2, system call retry
      is signalled through :data:`errno.EINTR`. The invocation is automatically
      restarted.
    * When performing IO against a TTY, disconnection of the remote end is
      signalled by :data:`errno.EIO`.
    * When performing IO against a socket, disconnection of the remote end is
      signalled by :data:`errno.ECONNRESET`.
    * When performing IO against a pipe, disconnection of the remote end is
      signalled by :data:`errno.EPIPE`.

    :returns:
        Tuple of `(return_value, disconnected)`, where `return_value` is the
        return value of `func(*args)`, and `disconnected` is :data:`True` if
        disconnection was detected, otherwise :data:`False`.
    """
    while True:
        try:
            return func(*args), False
        except (select.error, OSError, IOError):
            e = sys.exc_info()[1]
            _vv and IOLOG.debug('io_op(%r) -> OSError: %s', func, e)
            if e.args[0] == errno.EINTR:
                continue
            if e.args[0] in (errno.EIO, errno.ECONNRESET, errno.EPIPE):
                return None, True
            raise


class PidfulStreamHandler(logging.StreamHandler):
    """A :class:`logging.StreamHandler` subclass used when
    :meth:`Router.enable_debug() <mitogen.master.Router.enable_debug>` has been
    called, or the `debug` parameter was specified during context construction.
    Verifies the process ID has not changed on each call to :meth:`emit`,
    reopening the associated log file when a change is detected.

    This ensures logging to the per-process output files happens correctly even
    when uncooperative third party components call :func:`os.fork`.
    """
    #: PID that last opened the log file.
    open_pid = None

    #: Output path template.
    template = '/tmp/mitogen.%s.%s.log'

    def _reopen(self):
        self.acquire()
        try:
            if self.open_pid == os.getpid():
                return
            ts = time.strftime('%Y%m%d_%H%M%S')
            path = self.template % (os.getpid(), ts)
            self.stream = open(path, 'w', 1)
            set_cloexec(self.stream.fileno())
            self.stream.write('Parent PID: %s\n' % (os.getppid(),))
            self.stream.write('Created by:\n\n%s\n' % (
                ''.join(traceback.format_stack()),
            ))
            self.open_pid = os.getpid()
        finally:
            self.release()

    def emit(self, record):
        if self.open_pid != os.getpid():
            self._reopen()
        logging.StreamHandler.emit(self, record)


def enable_debug_logging():
    global _v, _vv
    _v = True
    _vv = True
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    IOLOG.setLevel(logging.DEBUG)
    handler = PidfulStreamHandler()
    handler.formatter = logging.Formatter(
        '%(asctime)s %(levelname).1s %(name)s: %(message)s',
        '%H:%M:%S'
    )
    root.handlers.insert(0, handler)


_profile_hook = lambda name, func, *args: func(*args)


def enable_profiling():
    global _profile_hook
    import cProfile
    import pstats
    def _profile_hook(name, func, *args):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return func(*args)
        finally:
            profiler.dump_stats('/tmp/mitogen.%d.%s.pstat' % (os.getpid(), name))
            profiler.create_stats()
            fp = open('/tmp/mitogen.stats.%d.%s.log' % (os.getpid(), name), 'w')
            try:
                stats = pstats.Stats(profiler, stream=fp)
                stats.sort_stats('cumulative')
                stats.print_stats()
            finally:
                fp.close()


def import_module(modname):
    """
    Import `module` and return the attribute named `attr`.
    """
    return __import__(modname, None, None, [''])


if PY3:
    # In 3.x Unpickler is a class exposing find_class as an overridable, but it
    # cannot be overridden without subclassing.
    class _Unpickler(pickle.Unpickler):
        def find_class(self, module, func):
            return self.find_global(module, func)
else:
    # In 2.x Unpickler is a function exposing a writeable find_global
    # attribute.
    _Unpickler = pickle.Unpickler


class Message(object):
    dst_id = None
    src_id = None
    auth_id = None
    handle = None
    reply_to = None
    data = b('')
    _unpickled = object()

    router = None
    receiver = None

    def __init__(self, **kwargs):
        self.src_id = mitogen.context_id
        self.auth_id = mitogen.context_id
        vars(self).update(kwargs)
        assert isinstance(self.data, BytesType)

    def _unpickle_context(self, context_id, name):
        return _unpickle_context(self.router, context_id, name)

    def _unpickle_sender(self, context_id, dst_handle):
        return _unpickle_sender(self.router, context_id, dst_handle)

    def _unpickle_bytes(self, s, encoding):
        s, n = LATIN1_CODEC.encode(s)
        return s

    def _find_global(self, module, func):
        """Return the class implementing `module_name.class_name` or raise
        `StreamError` if the module is not whitelisted."""
        if module == __name__:
            if func == '_unpickle_call_error':
                return _unpickle_call_error
            elif func == '_unpickle_sender':
                return self._unpickle_sender
            elif func == '_unpickle_context':
                return self._unpickle_context
            elif func == 'Blob':
                return Blob
            elif func == 'Secret':
                return Secret
            elif func == 'Kwargs':
                return Kwargs
        elif module == '_codecs' and func == 'encode':
            return self._unpickle_bytes
        elif module == '__builtin__' and func == 'bytes':
            return BytesType
        raise StreamError('cannot unpickle %r/%r', module, func)

    @property
    def is_dead(self):
        return self.reply_to == IS_DEAD

    @classmethod
    def dead(cls, **kwargs):
        return cls(reply_to=IS_DEAD, **kwargs)

    @classmethod
    def pickled(cls, obj, **kwargs):
        self = cls(**kwargs)
        try:
            self.data = pickle.dumps(obj, protocol=2)
        except pickle.PicklingError:
            e = sys.exc_info()[1]
            self.data = pickle.dumps(CallError(e), protocol=2)
        return self

    def reply(self, msg, router=None, **kwargs):
        if not isinstance(msg, Message):
            msg = Message.pickled(msg)
        msg.dst_id = self.src_id
        msg.handle = self.reply_to
        vars(msg).update(kwargs)
        if msg.handle:
            (self.router or router).route(msg)
        else:
            LOG.debug('Message.reply(): discarding due to zero handle: %r', msg)

    if PY3:
        UNPICKLER_KWARGS = {'encoding': 'bytes'}
    else:
        UNPICKLER_KWARGS = {}

    def unpickle(self, throw=True, throw_dead=True):
        """Deserialize `data` into an object."""
        _vv and IOLOG.debug('%r.unpickle()', self)
        if throw_dead and self.is_dead:
            raise ChannelError(ChannelError.remote_msg)

        obj = self._unpickled
        if obj is Message._unpickled:
            fp = BytesIO(self.data)
            unpickler = _Unpickler(fp, **self.UNPICKLER_KWARGS)
            unpickler.find_global = self._find_global
            try:
                # Must occur off the broker thread.
                obj = unpickler.load()
                self._unpickled = obj
            except (TypeError, ValueError):
                e = sys.exc_info()[1]
                raise StreamError('invalid message: %s', e)

        if throw:
            if isinstance(obj, CallError):
                raise obj

        return obj

    def __repr__(self):
        return 'Message(%r, %r, %r, %r, %r, %r..%d)' % (
            self.dst_id, self.src_id, self.auth_id, self.handle,
            self.reply_to, (self.data or '')[:50], len(self.data)
        )


class Sender(object):
    def __init__(self, context, dst_handle):
        self.context = context
        self.dst_handle = dst_handle

    def __repr__(self):
        return 'Sender(%r, %r)' % (self.context, self.dst_handle)

    def __reduce__(self):
        return _unpickle_sender, (self.context.context_id, self.dst_handle)

    def close(self):
        """Indicate this channel is closed to the remote side."""
        _vv and IOLOG.debug('%r.close()', self)
        self.context.send(Message.dead(handle=self.dst_handle))

    def send(self, data):
        """Send `data` to the remote."""
        _vv and IOLOG.debug('%r.send(%r..)', self, repr(data)[:100])
        self.context.send(Message.pickled(data, handle=self.dst_handle))


def _unpickle_sender(router, context_id, dst_handle):
    if not (isinstance(router, Router) and
            isinstance(context_id, (int, long)) and context_id >= 0 and
            isinstance(dst_handle, (int, long)) and dst_handle > 0):
        raise TypeError('cannot unpickle Sender: bad input')
    return Sender(Context(router, context_id), dst_handle)


class Receiver(object):
    notify = None
    raise_channelerror = True

    def __init__(self, router, handle=None, persist=True,
                 respondent=None, policy=None):
        self.router = router
        self.handle = handle  # Avoid __repr__ crash in add_handler()
        self._latch = Latch()  # Must exist prior to .add_handler()
        self.handle = router.add_handler(
            fn=self._on_receive,
            handle=handle,
            policy=policy,
            persist=persist,
            respondent=respondent,
        )

    def __repr__(self):
        return 'Receiver(%r, %r)' % (self.router, self.handle)

    def to_sender(self):
        context = Context(self.router, mitogen.context_id)
        return Sender(context, self.handle)

    def _on_receive(self, msg):
        """Callback from the Stream; appends data to the internal queue."""
        _vv and IOLOG.debug('%r._on_receive(%r)', self, msg)
        self._latch.put(msg)
        if self.notify:
            self.notify(self)

    def close(self):
        if self.handle:
            self.router.del_handler(self.handle)
            self.handle = None
        self._latch.put(Message.dead())

    def empty(self):
        return self._latch.empty()

    def get(self, timeout=None, block=True, throw_dead=True):
        _vv and IOLOG.debug('%r.get(timeout=%r, block=%r)', self, timeout, block)
        msg = self._latch.get(timeout=timeout, block=block)
        if msg.is_dead and throw_dead:
            if msg.src_id == mitogen.context_id:
                raise ChannelError(ChannelError.local_msg)
            else:
                raise ChannelError(ChannelError.remote_msg)
        return msg

    def __iter__(self):
        while True:
            msg = self.get(throw_dead=False)
            if msg.is_dead:
                return
            yield msg


class Channel(Sender, Receiver):
    def __init__(self, router, context, dst_handle, handle=None):
        Sender.__init__(self, context, dst_handle)
        Receiver.__init__(self, router, handle)

    def __repr__(self):
        return 'Channel(%s, %s)' % (
            Sender.__repr__(self),
            Receiver.__repr__(self)
        )


class Importer(object):
    """
    Import protocol implementation that fetches modules from the parent
    process.

    :param context: Context to communicate via.
    """
    def __init__(self, router, context, core_src, whitelist=(), blacklist=()):
        self._context = context
        self._present = {'mitogen': [
            'compat',
            'debug',
            'doas',
            'docker',
            'kubectl',
            'fakessh',
            'fork',
            'jail',
            'lxc',
            'lxd',
            'master',
            'minify',
            'parent',
            'select',
            'service',
            'setns',
            'ssh',
            'su',
            'sudo',
            'utils',
        ]}
        self._lock = threading.Lock()
        self.whitelist = list(whitelist) or ['']
        self.blacklist = list(blacklist) + [
            # 2.x generates needless imports for 'builtins', while 3.x does the
            # same for '__builtin__'. The correct one is built-in, the other
            # always a negative round-trip.
            'builtins',
            '__builtin__',
            # org.python.core imported by copy, pickle, xml.sax; breaks Jython,
            # but very unlikely to trigger a bug report.
            'org',
        ]
        if PY3:
            self.blacklist += ['cStringIO']

        # Presence of an entry in this map indicates in-flight GET_MODULE.
        self._callbacks = {}
        self._cache = {}
        if core_src:
            self._cache['mitogen.core'] = (
                'mitogen.core',
                None,
                'mitogen/core.py',
                zlib.compress(core_src, 9),
                [],
            )
        self._install_handler(router)

    def _install_handler(self, router):
        router.add_handler(
            fn=self._on_load_module,
            handle=LOAD_MODULE,
            policy=has_parent_authority,
        )

    def __repr__(self):
        return 'Importer()'

    def builtin_find_module(self, fullname):
        # imp.find_module() will always succeed for __main__, because it is a
        # built-in module. That means it exists on a special linked list deep
        # within the bowels of the interpreter. We must special case it.
        if fullname == '__main__':
            raise ImportError()

        parent, _, modname = fullname.rpartition('.')
        if parent:
            path = sys.modules[parent].__path__
        else:
            path = None

        fp, pathname, description = imp.find_module(modname, path)
        if fp:
            fp.close()

    def find_module(self, fullname, path=None):
        if hasattr(_tls, 'running'):
            return None

        _tls.running = True
        try:
            _v and LOG.debug('%r.find_module(%r)', self, fullname)
            pkgname, dot, _ = fullname.rpartition('.')
            pkg = sys.modules.get(pkgname)
            if pkgname and getattr(pkg, '__loader__', None) is not self:
                LOG.debug('%r: %r is submodule of a package we did not load',
                          self, fullname)
                return None

            suffix = fullname[len(pkgname+dot):]
            if pkgname and suffix not in self._present.get(pkgname, ()):
                LOG.debug('%r: master doesn\'t know %r', self, fullname)
                return None

            # #114: explicitly whitelisted prefixes override any
            # system-installed package.
            if self.whitelist != ['']:
                if any(fullname.startswith(s) for s in self.whitelist):
                    return self

            try:
                self.builtin_find_module(fullname)
                _vv and IOLOG.debug('%r: %r is available locally',
                                    self, fullname)
            except ImportError:
                _vv and IOLOG.debug('find_module(%r) returning self', fullname)
                return self
        finally:
            del _tls.running

    def _refuse_imports(self, fullname):
        if is_blacklisted_import(self, fullname):
            raise ImportError('Refused: ' + fullname)

        f = sys._getframe(2)
        requestee = f.f_globals['__name__']

        if fullname == '__main__' and requestee == 'pkg_resources':
            # Anything that imports pkg_resources will eventually cause
            # pkg_resources to try and scan __main__ for its __requires__
            # attribute (pkg_resources/__init__.py::_build_master()). This
            # breaks any app that is not expecting its __main__ to suddenly be
            # sucked over a network and injected into a remote process, like
            # py.test.
            raise ImportError('Refused')

        if fullname == 'pbr':
            # It claims to use pkg_resources to read version information, which
            # would result in PEP-302 being used, but it actually does direct
            # filesystem access. So instead smodge the environment to override
            # any version that was defined. This will probably break something
            # later.
            os.environ['PBR_VERSION'] = '0.0.0'

    def _on_load_module(self, msg):
        if msg.is_dead:
            return

        tup = msg.unpickle()
        fullname = tup[0]
        _v and LOG.debug('Importer._on_load_module(%r)', fullname)

        self._lock.acquire()
        try:
            self._cache[fullname] = tup
            callbacks = self._callbacks.pop(fullname, [])
        finally:
            self._lock.release()

        for callback in callbacks:
            callback()

    def _request_module(self, fullname, callback):
        self._lock.acquire()
        try:
            present = fullname in self._cache
            if not present:
                funcs = self._callbacks.get(fullname)
                if funcs is not None:
                    _v and LOG.debug('_request_module(%r): in flight', fullname)
                    funcs.append(callback)
                else:
                    _v and LOG.debug('_request_module(%r): new request', fullname)
                    self._callbacks[fullname] = [callback]
                    self._context.send(
                        Message(data=b(fullname), handle=GET_MODULE)
                    )
        finally:
            self._lock.release()

        if present:
            callback()

    def load_module(self, fullname):
        fullname = to_text(fullname)
        _v and LOG.debug('Importer.load_module(%r)', fullname)
        self._refuse_imports(fullname)

        event = threading.Event()
        self._request_module(fullname, event.set)
        event.wait()

        ret = self._cache[fullname]
        if ret[2] is None:
            raise ImportError('Master does not have %r' % (fullname,))

        pkg_present = ret[1]
        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
        mod.__file__ = self.get_filename(fullname)
        mod.__loader__ = self
        if pkg_present is not None:  # it's a package.
            mod.__path__ = []
            mod.__package__ = fullname
            self._present[fullname] = pkg_present
        else:
            mod.__package__ = fullname.rpartition('.')[0] or None

        if mod.__package__ and not PY3:
            # 2.x requires __package__ to be exactly a string.
            mod.__package__ = mod.__package__.encode()

        source = self.get_source(fullname)
        code = compile(source, mod.__file__, 'exec', 0, 1)
        if PY3:
            exec(code, vars(mod))
        else:
            exec('exec code in vars(mod)')
        return mod

    def get_filename(self, fullname):
        if fullname in self._cache:
            path = self._cache[fullname][2]
            if path is None:
                # If find_loader() returns self but a subsequent master RPC
                # reveals the module can't be loaded, and so load_module()
                # throws ImportError, on Python 3.x it is still possible for
                # the loader to be called to fetch metadata.
                raise ImportError('master cannot serve %r' % (fullname,))
            return u'master:' + self._cache[fullname][2]

    def get_source(self, fullname):
        if fullname in self._cache:
            compressed = self._cache[fullname][3]
            if compressed is None:
                raise ImportError('master cannot serve %r' % (fullname,))

            source = zlib.decompress(self._cache[fullname][3])
            if PY3:
                return to_text(source)
            return source


class LogHandler(logging.Handler):
    def __init__(self, context):
        logging.Handler.__init__(self)
        self.context = context
        self.local = threading.local()
        self._buffer = []

    def uncork(self):
        self._send = self.context.send
        for msg in self._buffer:
            self._send(msg)
        self._buffer = None

    def _send(self, msg):
        self._buffer.append(msg)

    def emit(self, rec):
        if rec.name == 'mitogen.io' or \
           getattr(self.local, 'in_emit', False):
            return

        self.local.in_emit = True
        try:
            msg = self.format(rec)
            encoded = '%s\x00%s\x00%s' % (rec.name, rec.levelno, msg)
            if isinstance(encoded, UnicodeType):
                # Logging package emits both :(
                encoded = encoded.encode('utf-8')
            self._send(Message(data=encoded, handle=FORWARD_LOG))
        finally:
            self.local.in_emit = False


class Side(object):
    _fork_refs = weakref.WeakValueDictionary()

    def __init__(self, stream, fd, cloexec=True, keep_alive=True, blocking=False):
        self.stream = stream
        self.fd = fd
        self.closed = False
        self.keep_alive = keep_alive
        self._fork_refs[id(self)] = self
        if cloexec:
            set_cloexec(fd)
        if not blocking:
            set_nonblock(fd)

    def __repr__(self):
        return '<Side of %r fd %s>' % (self.stream, self.fd)

    @classmethod
    def _on_fork(cls):
        for side in list(cls._fork_refs.values()):
            side.close()

    def close(self):
        if not self.closed:
            _vv and IOLOG.debug('%r.close()', self)
            self.closed = True
            os.close(self.fd)

    def read(self, n=CHUNK_SIZE):
        if self.closed:
            # Refuse to touch the handle after closed, it may have been reused
            # by another thread. TODO: synchronize read()/write()/close().
            return b('')
        s, disconnected = io_op(os.read, self.fd, n)
        if disconnected:
            return b('')
        return s

    def write(self, s):
        if self.closed or self.fd is None:
            # Refuse to touch the handle after closed, it may have been reused
            # by another thread.
            return None

        written, disconnected = io_op(os.write, self.fd, s)
        if disconnected:
            return None
        return written


class BasicStream(object):
    receive_side = None
    transmit_side = None

    def on_disconnect(self, broker):
        LOG.debug('%r.on_disconnect()', self)
        if self.receive_side:
            broker.stop_receive(self)
            self.receive_side.close()
        if self.transmit_side:
            broker._stop_transmit(self)
            self.transmit_side.close()
        fire(self, 'disconnect')

    def on_shutdown(self, broker):
        _v and LOG.debug('%r.on_shutdown()', self)
        fire(self, 'shutdown')
        self.on_disconnect(broker)


class Stream(BasicStream):
    """
    :py:class:`BasicStream` subclass implementing mitogen's :ref:`stream
    protocol <stream-protocol>`.
    """
    #: If not :data:`None`, :py:class:`Router` stamps this into
    #: :py:attr:`Message.auth_id` of every message received on this stream.
    auth_id = None

    #: If not :data:`False`, indicates the stream has :attr:`auth_id` set and
    #: its value is the same as :data:`mitogen.context_id` or appears in
    #: :data:`mitogen.parent_ids`.
    is_privileged = False

    def __init__(self, router, remote_id, **kwargs):
        self._router = router
        self.remote_id = remote_id
        self.name = u'default'
        self.sent_modules = set(['mitogen', 'mitogen.core'])
        self.construct(**kwargs)
        self._input_buf = collections.deque()
        self._output_buf = collections.deque()
        self._input_buf_len = 0
        self._output_buf_len = 0
        #: Routing records the dst_id of every message arriving from this
        #: stream. Any arriving DEL_ROUTE is rebroadcast for any such ID.
        self.egress_ids = set()

    def construct(self):
        pass

    def _internal_receive(self, broker, buf):
        if self._input_buf and self._input_buf_len < 128:
            self._input_buf[0] += buf
        else:
            self._input_buf.append(buf)

        self._input_buf_len += len(buf)
        while self._receive_one(broker):
            pass

    def on_receive(self, broker):
        """Handle the next complete message on the stream. Raise
        :py:class:`StreamError` on failure."""
        _vv and IOLOG.debug('%r.on_receive()', self)

        buf = self.receive_side.read()
        if not buf:
            return self.on_disconnect(broker)

        self._internal_receive(broker, buf)

    HEADER_FMT = '>LLLLLL'
    HEADER_LEN = struct.calcsize(HEADER_FMT)

    def _receive_one(self, broker):
        if self._input_buf_len < self.HEADER_LEN:
            return False

        msg = Message()
        msg.router = self._router
        (msg.dst_id, msg.src_id, msg.auth_id,
         msg.handle, msg.reply_to, msg_len) = struct.unpack(
            self.HEADER_FMT,
            self._input_buf[0][:self.HEADER_LEN],
        )

        if msg_len > self._router.max_message_size:
            LOG.error('Maximum message size exceeded (got %d, max %d)',
                      msg_len, self._router.max_message_size)
            self.on_disconnect(broker)
            return False

        total_len = msg_len + self.HEADER_LEN
        if self._input_buf_len < total_len:
            _vv and IOLOG.debug(
                '%r: Input too short (want %d, got %d)',
                self, msg_len, self._input_buf_len - self.HEADER_LEN
            )
            return False

        start = self.HEADER_LEN
        prev_start = start
        remain = total_len
        bits = []
        while remain:
            buf = self._input_buf.popleft()
            bit = buf[start:remain]
            bits.append(bit)
            remain -= len(bit) + start
            prev_start = start
            start = 0

        msg.data = b('').join(bits)
        self._input_buf.appendleft(buf[prev_start+len(bit):])
        self._input_buf_len -= total_len
        self._router._async_route(msg, self)
        return True

    def pending_bytes(self):
        return self._output_buf_len

    def on_transmit(self, broker):
        """Transmit buffered messages."""
        _vv and IOLOG.debug('%r.on_transmit()', self)

        if self._output_buf:
            buf = self._output_buf.popleft()
            written = self.transmit_side.write(buf)
            if not written:
                _v and LOG.debug('%r.on_transmit(): disconnection detected', self)
                self.on_disconnect(broker)
                return
            elif written != len(buf):
                self._output_buf.appendleft(BufferType(buf, written))

            _vv and IOLOG.debug('%r.on_transmit() -> len %d', self, written)
            self._output_buf_len -= written

        if not self._output_buf:
            broker._stop_transmit(self)

    def _send(self, msg):
        _vv and IOLOG.debug('%r._send(%r)', self, msg)
        pkt = struct.pack(self.HEADER_FMT, msg.dst_id, msg.src_id,
                          msg.auth_id, msg.handle, msg.reply_to or 0,
                          len(msg.data)) + msg.data
        if not self._output_buf_len:
            self._router.broker._start_transmit(self)
        self._output_buf.append(pkt)
        self._output_buf_len += len(pkt)

    def send(self, msg):
        """Send `data` to `handle`, and tell the broker we have output. May
        be called from any thread."""
        self._router.broker.defer(self._send, msg)

    def on_shutdown(self, broker):
        """Override BasicStream behaviour of immediately disconnecting."""
        _v and LOG.debug('%r.on_shutdown(%r)', self, broker)

    def accept(self, rfd, wfd):
        # TODO: what is this os.dup for?
        self.receive_side = Side(self, os.dup(rfd))
        self.transmit_side = Side(self, os.dup(wfd))

    def __repr__(self):
        cls = type(self)
        return '%s.%s(%r)' % (cls.__module__, cls.__name__, self.name)


class Context(object):
    remote_name = None

    def __init__(self, router, context_id, name=None):
        self.router = router
        self.context_id = context_id
        self.name = name

    def __reduce__(self):
        name = self.name
        if name and not isinstance(name, UnicodeType):
            name = UnicodeType(name, 'utf-8')
        return _unpickle_context, (self.context_id, name)

    def on_disconnect(self):
        _v and LOG.debug('%r.on_disconnect()', self)
        fire(self, 'disconnect')

    def send_async(self, msg, persist=False):
        if self.router.broker._thread == threading.currentThread():  # TODO
            raise SystemError('Cannot making blocking call on broker thread')

        receiver = Receiver(self.router, persist=persist, respondent=self)
        msg.dst_id = self.context_id
        msg.reply_to = receiver.handle

        _v and LOG.debug('%r.send_async(%r)', self, msg)
        self.send(msg)
        return receiver

    def call_service_async(self, service_name, method_name, **kwargs):
        _v and LOG.debug('%r.call_service_async(%r, %r, %r)',
                         self, service_name, method_name, kwargs)
        if isinstance(service_name, BytesType):
            service_name = service_name.encode('utf-8')
        elif not isinstance(service_name, UnicodeType):
            service_name = service_name.name()  # Service.name()
        tup = (service_name, to_text(method_name), Kwargs(kwargs))
        msg = Message.pickled(tup, handle=CALL_SERVICE)
        return self.send_async(msg)

    def send(self, msg):
        """send `obj` to `handle`, and tell the broker we have output. May
        be called from any thread."""
        msg.dst_id = self.context_id
        self.router.route(msg)

    def call_service(self, service_name, method_name, **kwargs):
        recv = self.call_service_async(service_name, method_name, **kwargs)
        return recv.get().unpickle()

    def send_await(self, msg, deadline=None):
        """Send `msg` and wait for a response with an optional timeout."""
        receiver = self.send_async(msg)
        response = receiver.get(deadline)
        data = response.unpickle()
        _vv and IOLOG.debug('%r._send_await() -> %r', self, data)
        return data

    def __repr__(self):
        return 'Context(%s, %r)' % (self.context_id, self.name)


def _unpickle_context(router, context_id, name):
    if not (isinstance(router, Router) and
            isinstance(context_id, (int, long)) and context_id >= 0 and (
                (name is None) or
                (isinstance(name, UnicodeType) and len(name) < 100))
            ):
        raise TypeError('cannot unpickle Context: bad input')
    return router.context_by_id(context_id, name=name)


class Poller(object):
    #: Increments on every poll(). Used to version _rfds and _wfds.
    _generation = 1

    def __init__(self):
        self._rfds = {}
        self._wfds = {}

    @property
    def readers(self):
        return list((fd, data) for fd, (data, gen) in self._rfds.items())

    @property
    def writers(self):
        return list((fd, data) for fd, (data, gen) in self._wfds.items())

    def __repr__(self):
        return '%s(%#x)' % (type(self).__name__, id(self))

    def close(self):
        pass

    def start_receive(self, fd, data=None):
        self._rfds[fd] = (data or fd, self._generation)

    def stop_receive(self, fd):
        self._rfds.pop(fd, None)

    def start_transmit(self, fd, data=None):
        self._wfds[fd] = (data or fd, self._generation)

    def stop_transmit(self, fd):
        self._wfds.pop(fd, None)

    def _poll(self, timeout):
        (rfds, wfds, _), _ = io_op(select.select,
            self._rfds,
            self._wfds,
            (), timeout
        )

        for fd in rfds:
            _vv and IOLOG.debug('%r: POLLIN for %r', self, fd)
            data, gen = self._rfds.get(fd, (None, None))
            if gen and gen < self._generation:
                yield data

        for fd in wfds:
            _vv and IOLOG.debug('%r: POLLOUT for %r', self, fd)
            data, gen = self._wfds.get(fd, (None, None))
            if gen and gen < self._generation:
                yield data

    def poll(self, timeout=None):
        _vv and IOLOG.debug('%r.poll(%r)', self, timeout)
        self._generation += 1
        return self._poll(timeout)


class Latch(object):
    """
    A latch is a :py:class:`Queue.Queue`-like object that supports mutation and
    waiting from multiple threads, however unlike :py:class:`Queue.Queue`,
    waiting threads always remain interruptible, so CTRL+C always succeeds, and
    waits where a timeout is set experience no wake up latency. These
    properties are not possible in combination using the built-in threading
    primitives available in Python 2.x.

    Latches implement queues using the UNIX self-pipe trick, and a per-thread
    :py:func:`socket.socketpair` that is lazily created the first time any
    latch attempts to sleep on a thread, and dynamically associated with the
    waiting Latch only for duration of the wait.

    See :ref:`waking-sleeping-threads` for further discussion.
    """
    poller_class = Poller

    # The _cls_ prefixes here are to make it crystal clear in the code which
    # state mutation isn't covered by :attr:`_lock`.

    #: List of reusable :func:`socket.socketpair` tuples. The list is from
    #: multiple threads, the only safe operations are `append()` and `pop()`.
    _cls_idle_socketpairs = []

    #: List of every socket object that must be closed by :meth:`_on_fork`.
    #: Inherited descriptors cannot be reused, as the duplicated handles
    #: reference the same underlying kernel-side sockets still in use by
    #: the parent process.
    _cls_all_sockets = []

    def __init__(self):
        self.closed = False
        self._lock = threading.Lock()
        #: List of unconsumed enqueued items.
        self._queue = []
        #: List of `(wsock, cookie)` awaiting an element, where `wsock` is the
        #: socketpair's write side, and `cookie` is the string to write.
        self._sleeping = []
        #: Number of elements of :attr:`_sleeping` that have already been
        #: woken, and have a corresponding element index from :attr:`_queue`
        #: assigned to them.
        self._waking = 0

    @classmethod
    def _on_fork(cls):
        """
        Clean up any files belonging to the parent process after a fork.
        """
        cls._cls_idle_socketpairs = []
        while cls._cls_all_sockets:
            cls._cls_all_sockets.pop().close()

    def close(self):
        """
        Mark the latch as closed, and cause every sleeping thread to be woken,
        with :py:class:`mitogen.core.LatchError` raised in each thread.
        """
        self._lock.acquire()
        try:
            self.closed = True
            while self._waking < len(self._sleeping):
                wsock, cookie = self._sleeping[self._waking]
                self._wake(wsock, cookie)
                self._waking += 1
        finally:
            self._lock.release()

    def empty(self):
        """
        Return :py:data:`True` if calling :py:meth:`get` would block.

        As with :py:class:`Queue.Queue`, :py:data:`True` may be returned even
        though a subsequent call to :py:meth:`get` will succeed, since a
        message may be posted at any moment between :py:meth:`empty` and
        :py:meth:`get`.

        As with :py:class:`Queue.Queue`, :py:data:`False` may be returned even
        though a subsequent call to :py:meth:`get` will block, since another
        waiting thread may be woken at any moment between :py:meth:`empty` and
        :py:meth:`get`.
        """
        return len(self._queue) == 0

    def _get_socketpair(self):
        """
        Return an unused socketpair, creating one if none exist.
        """
        try:
            return self._cls_idle_socketpairs.pop()  # pop() must be atomic
        except IndexError:
            rsock, wsock = socket.socketpair()
            set_cloexec(rsock.fileno())
            set_cloexec(wsock.fileno())
            self._cls_all_sockets.extend((rsock, wsock))
            return rsock, wsock

    COOKIE_SIZE = 33

    def _make_cookie(self):
        """
        Return a 33-byte string encoding the ID of the instance and the current
        thread. This disambiguates legitimate wake-ups, accidental writes to
        the FD, and buggy internal FD sharing.
        """
        ident = threading.currentThread().ident
        return b(u'%016x-%016x' % (int(id(self)), ident))

    def get(self, timeout=None, block=True):
        """
        Return the next enqueued object, or sleep waiting for one.

        :param float timeout:
            If not :py:data:`None`, specifies a timeout in seconds.

        :param bool block:
            If :py:data:`False`, immediately raise
            :py:class:`mitogen.core.TimeoutError` if the latch is empty.

        :raises mitogen.core.LatchError:
            :py:meth:`close` has been called, and the object is no longer valid.

        :raises mitogen.core.TimeoutError:
            Timeout was reached.

        :returns:
            The de-queued object.
        """
        _vv and IOLOG.debug('%r.get(timeout=%r, block=%r)',
                            self, timeout, block)
        self._lock.acquire()
        try:
            if self.closed:
                raise LatchError()
            i = len(self._sleeping)
            if len(self._queue) > i:
                _vv and IOLOG.debug('%r.get() -> %r', self, self._queue[i])
                return self._queue.pop(i)
            if not block:
                raise TimeoutError()
            rsock, wsock = self._get_socketpair()
            cookie = self._make_cookie()
            self._sleeping.append((wsock, cookie))
        finally:
            self._lock.release()

        poller = self.poller_class()
        poller.start_receive(rsock.fileno())
        try:
            return self._get_sleep(poller, timeout, block, rsock, wsock, cookie)
        finally:
            poller.close()

    def _get_sleep(self, poller, timeout, block, rsock, wsock, cookie):
        """
        When a result is not immediately available, sleep waiting for
        :meth:`put` to write a byte to our socket pair.
        """
        _vv and IOLOG.debug(
            '%r._get_sleep(timeout=%r, block=%r, rfd=%d, wfd=%d)',
            self, timeout, block, rsock.fileno(), wsock.fileno()
        )

        e = None
        woken = None
        try:
            woken = list(poller.poll(timeout))
        except Exception:
            e = sys.exc_info()[1]

        self._lock.acquire()
        try:
            i = self._sleeping.index((wsock, cookie))
            del self._sleeping[i]
            if not woken:
                raise e or TimeoutError()

            got_cookie = rsock.recv(self.COOKIE_SIZE)
            self._cls_idle_socketpairs.append((rsock, wsock))

            assert cookie == got_cookie, (
                "Cookie incorrect; got %r, expected %r" \
                % (got_cookie, cookie)
            )
            assert i < self._waking, (
                "Cookie correct, but no queue element assigned."
            )
            self._waking -= 1
            if self.closed:
                raise LatchError()
            _vv and IOLOG.debug('%r.get() wake -> %r', self, self._queue[i])
            return self._queue.pop(i)
        finally:
            self._lock.release()

    def put(self, obj):
        """
        Enqueue an object, waking the first thread waiting for a result, if one
        exists.

        :raises mitogen.core.LatchError:
            :py:meth:`close` has been called, and the object is no longer valid.
        """
        _vv and IOLOG.debug('%r.put(%r)', self, obj)
        self._lock.acquire()
        try:
            if self.closed:
                raise LatchError()
            self._queue.append(obj)

            if self._waking < len(self._sleeping):
                wsock, cookie = self._sleeping[self._waking]
                self._waking += 1
                _vv and IOLOG.debug('%r.put() -> waking wfd=%r',
                                    self, wsock.fileno())
                self._wake(wsock, cookie)
        finally:
            self._lock.release()

    def _wake(self, wsock, cookie):
        try:
            os.write(wsock.fileno(), cookie)
        except OSError:
            e = sys.exc_info()[1]
            if e.args[0] != errno.EBADF:
                raise

    def __repr__(self):
        return 'Latch(%#x, size=%d, t=%r)' % (
            id(self),
            len(self._queue),
            threading.currentThread().name,
        )


class Waker(BasicStream):
    """
    :py:class:`BasicStream` subclass implementing the `UNIX self-pipe trick`_.
    Used to wake the multiplexer when another thread needs to modify its state
    (via a cross-thread function call).

    .. _UNIX self-pipe trick: https://cr.yp.to/docs/selfpipe.html
    """
    broker_ident = None

    def __init__(self, broker):
        self._broker = broker
        self._lock = threading.Lock()
        self._deferred = []

        rfd, wfd = os.pipe()
        self.receive_side = Side(self, rfd)
        self.transmit_side = Side(self, wfd)

    def __repr__(self):
        return 'Waker(%r rfd=%r, wfd=%r)' % (
            self._broker,
            self.receive_side.fd,
            self.transmit_side.fd,
        )

    @property
    def keep_alive(self):
        """
        Prevent immediate Broker shutdown while deferred functions remain.
        """
        self._lock.acquire()
        try:
            return len(self._deferred)
        finally:
            self._lock.release()

    def on_receive(self, broker):
        """
        Drain the pipe and fire callbacks. Reading multiple bytes is safe since
        new bytes corresponding to future .defer() calls are written only after
        .defer() takes _lock: either a byte we read corresponds to something
        already on the queue by the time we take _lock, or a byte remains
        buffered, causing another wake up, because it was written after we
        released _lock.
        """
        _vv and IOLOG.debug('%r.on_receive()', self)
        self.receive_side.read(128)
        self._lock.acquire()
        try:
            deferred = self._deferred
            self._deferred = []
        finally:
            self._lock.release()

        for func, args, kwargs in deferred:
            try:
                func(*args, **kwargs)
            except Exception:
                LOG.exception('defer() crashed: %r(*%r, **%r)',
                              func, args, kwargs)
                self._broker.shutdown()

    def defer(self, func, *args, **kwargs):
        if threading.currentThread().ident == self.broker_ident:
            _vv and IOLOG.debug('%r.defer() [immediate]', self)
            return func(*args, **kwargs)

        _vv and IOLOG.debug('%r.defer() [fd=%r]', self, self.transmit_side.fd)
        self._lock.acquire()
        try:
            self._deferred.append((func, args, kwargs))
        finally:
            self._lock.release()

        # Wake the multiplexer by writing a byte. If the broker is in the midst
        # of tearing itself down, the waker fd may already have been closed, so
        # ignore EBADF here.
        try:
            self.transmit_side.write(b(' '))
        except OSError:
            e = sys.exc_info()[1]
            if e.args[0] != errno.EBADF:
                raise


class IoLogger(BasicStream):
    """
    :py:class:`BasicStream` subclass that sets up redirection of a standard
    UNIX file descriptor back into the Python :py:mod:`logging` package.
    """
    _buf = ''

    def __init__(self, broker, name, dest_fd):
        self._broker = broker
        self._name = name
        self._log = logging.getLogger(name)
        self._rsock, self._wsock = socket.socketpair()
        os.dup2(self._wsock.fileno(), dest_fd)
        set_cloexec(self._wsock.fileno())

        self.receive_side = Side(self, self._rsock.fileno())
        self.transmit_side = Side(self, dest_fd, cloexec=False, blocking=True)
        self._broker.start_receive(self)

    def __repr__(self):
        return '<IoLogger %s>' % (self._name,)

    def _log_lines(self):
        while self._buf.find('\n') != -1:
            line, _, self._buf = self._buf.partition('\n')
            self._log.info('%s', line.rstrip('\n'))

    def on_shutdown(self, broker):
        """Shut down the write end of the logging socket."""
        _v and LOG.debug('%r.on_shutdown()', self)
        self._wsock.shutdown(socket.SHUT_WR)
        self._wsock.close()
        self.transmit_side.close()

    def on_receive(self, broker):
        _vv and IOLOG.debug('%r.on_receive()', self)
        buf = self.receive_side.read()
        if not buf:
            return self.on_disconnect(broker)

        self._buf += buf.decode('latin1')
        self._log_lines()


class Router(object):
    context_class = Context
    max_message_size = 128 * 1048576
    unidirectional = False

    def __init__(self, broker):
        self.broker = broker
        listen(broker, 'exit', self._on_broker_exit)

        # Here seems as good a place as any.
        global _v, _vv
        _v = logging.getLogger().level <= logging.DEBUG
        _vv = IOLOG.level <= logging.DEBUG

        #: context ID -> Stream
        self._stream_by_id = {}
        #: List of contexts to notify of shutdown.
        self._context_by_id = {}
        self._last_handle = itertools.count(1000)
        #: handle -> (persistent?, func(msg))
        self._handle_map = {}
        self.add_handler(self._on_del_route, DEL_ROUTE)

    def __repr__(self):
        return 'Router(%r)' % (self.broker,)

    def _on_del_route(self, msg):
        """
        Stub DEL_ROUTE handler; fires 'disconnect' events on the corresponding
        member of :attr:`_context_by_id`. This handler is replaced by
        :class:`mitogen.parent.RouteMonitor` in an upgraded context.
        """
        LOG.error('%r._on_del_route() %r', self, msg)
        if not msg.is_dead:
            target_id_s, _, name = msg.data.partition(b(':'))
            target_id = int(target_id_s, 10)
            if target_id not in self._context_by_id:
                LOG.debug('DEL_ROUTE for unknown ID %r: %r', target_id, msg)
                return

            fire(self._context_by_id[target_id], 'disconnect')

    def on_stream_disconnect(self, stream):
        for context in self._context_by_id.values():
            stream_ = self._stream_by_id.get(context.context_id)
            if stream_ is stream:
                del self._stream_by_id[context.context_id]
                context.on_disconnect()

    def _on_broker_exit(self):
        while self._handle_map:
            _, (_, func, _) = self._handle_map.popitem()
            func(Message.dead())

    def context_by_id(self, context_id, via_id=None, create=True, name=None):
        context = self._context_by_id.get(context_id)
        if create and not context:
            context = self.context_class(self, context_id, name=name)
            if via_id is not None:
                context.via = self.context_by_id(via_id)
            self._context_by_id[context_id] = context
        return context

    def register(self, context, stream):
        _v and LOG.debug('register(%r, %r)', context, stream)
        self._stream_by_id[context.context_id] = stream
        self._context_by_id[context.context_id] = context
        self.broker.start_receive(stream)
        listen(stream, 'disconnect', lambda: self.on_stream_disconnect(stream))

    def stream_by_id(self, dst_id):
        return self._stream_by_id.get(dst_id,
            self._stream_by_id.get(mitogen.parent_id))

    def del_handler(self, handle):
        del self._handle_map[handle]

    def add_handler(self, fn, handle=None, persist=True,
                    policy=None, respondent=None):
        handle = handle or next(self._last_handle)
        _vv and IOLOG.debug('%r.add_handler(%r, %r, %r)', self, fn, handle, persist)

        if respondent:
            assert policy is None
            def policy(msg, _stream):
                return msg.is_dead or msg.src_id == respondent.context_id
            def on_disconnect():
                if handle in self._handle_map:
                    fn(Message.dead())
                    del self._handle_map[handle]
            listen(respondent, 'disconnect', on_disconnect)

        self._handle_map[handle] = persist, fn, policy
        return handle

    def on_shutdown(self, broker):
        """Called during :py:meth:`Broker.shutdown`, informs callbacks
        registered with :py:meth:`add_handle_cb` the connection is dead."""
        _v and LOG.debug('%r.on_shutdown(%r)', self, broker)
        fire(self, 'shutdown')
        for handle, (persist, fn) in self._handle_map.iteritems():
            _v and LOG.debug('%r.on_shutdown(): killing %r: %r', self, handle, fn)
            fn(Message.dead())

    refused_msg = 'Refused by policy.'

    def _invoke(self, msg, stream):
        # IOLOG.debug('%r._invoke(%r)', self, msg)
        try:
            persist, fn, policy = self._handle_map[msg.handle]
        except KeyError:
            LOG.error('%r: invalid handle: %r', self, msg)
            if msg.reply_to and not msg.is_dead:
                msg.reply(Message.dead())
            return

        if policy and not policy(msg, stream):
            LOG.error('%r: policy refused message: %r', self, msg)
            if msg.reply_to:
                self.route(Message.pickled(
                    CallError(self.refused_msg),
                    dst_id=msg.src_id,
                    handle=msg.reply_to
                ))
            return

        if not persist:
            del self._handle_map[msg.handle]

        try:
            fn(msg)
        except Exception:
            LOG.exception('%r._invoke(%r): %r crashed', self, msg, fn)

    def _maybe_send_dead(self, msg):
        if msg.reply_to and not msg.is_dead:
            msg.reply(Message.dead(), router=self)

    def _async_route(self, msg, in_stream=None):
        _vv and IOLOG.debug('%r._async_route(%r, %r)', self, msg, in_stream)

        if len(msg.data) > self.max_message_size:
            LOG.error('message too large (max %d bytes): %r',
                      self.max_message_size, msg)
            self._maybe_send_dead(msg)
            return

        # Perform source verification.
        if in_stream:
            parent = self._stream_by_id.get(mitogen.parent_id)
            expect = self._stream_by_id.get(msg.auth_id, parent)
            if in_stream != expect:
                LOG.error('%r: bad auth_id: got %r via %r, not %r: %r',
                          self, msg.auth_id, in_stream, expect, msg)
                return

            if msg.src_id != msg.auth_id:
                expect = self._stream_by_id.get(msg.src_id, parent)
                if in_stream != expect:
                    LOG.error('%r: bad src_id: got %r via %r, not %r: %r',
                              self, msg.src_id, in_stream, expect, msg)
                    return

            if in_stream.auth_id is not None:
                msg.auth_id = in_stream.auth_id

            # Maintain a set of IDs the source ever communicated with.
            in_stream.egress_ids.add(msg.dst_id)

        if msg.dst_id == mitogen.context_id:
            return self._invoke(msg, in_stream)

        out_stream = self._stream_by_id.get(msg.dst_id)
        if out_stream is None:
            out_stream = self._stream_by_id.get(mitogen.parent_id)

        if out_stream is None:
            if msg.reply_to not in (0, IS_DEAD):
                LOG.error('%r: no route for %r, my ID is %r',
                          self, msg, mitogen.context_id)
            self._maybe_send_dead(msg)
            return

        if in_stream and self.unidirectional and not \
                (in_stream.is_privileged or out_stream.is_privileged):
            LOG.error('routing mode prevents forward of %r from %r -> %r',
                      msg, in_stream, out_stream)
            self._maybe_send_dead(msg)
            return

        out_stream._send(msg)

    def route(self, msg):
        self.broker.defer(self._async_route, msg)


class Broker(object):
    poller_class = Poller
    _waker = None
    _thread = None
    shutdown_timeout = 3.0

    def __init__(self, poller_class=None):
        self._alive = True
        self._waker = Waker(self)
        self.defer = self._waker.defer
        self.poller = self.poller_class()
        self.poller.start_receive(
            self._waker.receive_side.fd,
            (self._waker.receive_side, self._waker.on_receive)
        )
        self._thread = threading.Thread(
            target=_profile_hook,
            args=('broker', self._broker_main),
            name='mitogen-broker'
        )
        self._thread.start()
        self._waker.broker_ident = self._thread.ident

    def start_receive(self, stream):
        _vv and IOLOG.debug('%r.start_receive(%r)', self, stream)
        side = stream.receive_side
        assert side and side.fd is not None
        self.defer(self.poller.start_receive,
                   side.fd, (side, stream.on_receive))

    def stop_receive(self, stream):
        _vv and IOLOG.debug('%r.stop_receive(%r)', self, stream)
        self.defer(self.poller.stop_receive, stream.receive_side.fd)

    def _start_transmit(self, stream):
        _vv and IOLOG.debug('%r._start_transmit(%r)', self, stream)
        side = stream.transmit_side
        assert side and side.fd is not None
        self.poller.start_transmit(side.fd, (side, stream.on_transmit))

    def _stop_transmit(self, stream):
        _vv and IOLOG.debug('%r._stop_transmit(%r)', self, stream)
        self.poller.stop_transmit(stream.transmit_side.fd)

    def keep_alive(self):
        it = (side.keep_alive for (_, (side, _)) in self.poller.readers)
        return sum(it, 0)

    def defer_sync(self, func):
        """
        Block the calling thread while `func` runs on a broker thread.

        :returns:
            Return value of `func()`.
        """
        latch = Latch()
        def wrapper():
            try:
                latch.put(func())
            except Exception:
                latch.put(sys.exc_info()[1])
        self.defer(wrapper)
        res = latch.get()
        if isinstance(res, Exception):
            raise res
        return res

    def _call(self, stream, func):
        try:
            func(self)
        except Exception:
            LOG.exception('%r crashed', stream)
            stream.on_disconnect(self)

    def _loop_once(self, timeout=None):
        _vv and IOLOG.debug('%r._loop_once(%r, %r)',
                            self, timeout, self.poller)
        #IOLOG.debug('readers =\n%s', pformat(self.poller.readers))
        #IOLOG.debug('writers =\n%s', pformat(self.poller.writers))
        for (side, func) in self.poller.poll(timeout):
            self._call(side.stream, func)

    def _broker_main(self):
        try:
            while self._alive:
                self._loop_once()

            fire(self, 'shutdown')
            for _, (side, _) in self.poller.readers + self.poller.writers:
                self._call(side.stream, side.stream.on_shutdown)

            deadline = time.time() + self.shutdown_timeout
            while self.keep_alive() and time.time() < deadline:
                self._loop_once(max(0, deadline - time.time()))

            if self.keep_alive():
                LOG.error('%r: some streams did not close gracefully. '
                          'The most likely cause for this is one or '
                          'more child processes still connected to '
                          'our stdout/stderr pipes.', self)

            for _, (side, _) in self.poller.readers + self.poller.writers:
                LOG.error('_broker_main() force disconnecting %r', side)
                side.stream.on_disconnect(self)
        except Exception:
            LOG.exception('_broker_main() crashed')

        fire(self, 'exit')

    def shutdown(self):
        _v and LOG.debug('%r.shutdown()', self)
        def _shutdown():
            self._alive = False
        self.defer(_shutdown)

    def join(self):
        self._thread.join()

    def __repr__(self):
        return 'Broker(%#x)' % (id(self),)


class Dispatcher(object):
    def __init__(self, econtext):
        self.econtext = econtext
        #: Chain ID -> CallError if prior call failed.
        self._error_by_chain_id = {}
        self.recv = Receiver(router=econtext.router,
                             handle=CALL_FUNCTION,
                             policy=has_parent_authority)
        listen(econtext.broker, 'shutdown', self.recv.close)

    @classmethod
    @takes_econtext
    def forget_chain(cls, chain_id, econtext):
        econtext.dispatcher._error_by_chain_id.pop(chain_id, None)

    def _parse_request(self, msg):
        data = msg.unpickle(throw=False)
        _v and LOG.debug('_dispatch_one(%r)', data)

        chain_id, modname, klass, func, args, kwargs = data
        obj = import_module(modname)
        if klass:
            obj = getattr(obj, klass)
        fn = getattr(obj, func)
        if getattr(fn, 'mitogen_takes_econtext', None):
            kwargs.setdefault('econtext', self.econtext)
        if getattr(fn, 'mitogen_takes_router', None):
            kwargs.setdefault('router', self.econtext.router)

        return chain_id, fn, args, kwargs

    def _dispatch_one(self, msg):
        try:
            chain_id, fn, args, kwargs = self._parse_request(msg)
        except Exception:
            return None, CallError(sys.exc_info()[1])

        if chain_id in self._error_by_chain_id:
            return chain_id, self._error_by_chain_id[chain_id]

        try:
            return chain_id, fn(*args, **kwargs)
        except Exception:
            e = CallError(sys.exc_info()[1])
            if chain_id is not None:
                self._error_by_chain_id[chain_id] = e
            return chain_id, e

    def _dispatch_calls(self):
        for msg in self.recv:
            chain_id, ret = self._dispatch_one(msg)
            _v and LOG.debug('_dispatch_calls: %r -> %r', msg, ret)
            if msg.reply_to:
                msg.reply(ret)
            elif isinstance(ret, CallError) and chain_id is None:
                LOG.error('No-reply function call failed: %s', ret)

    def run(self):
        if self.econtext.config.get('on_start'):
            self.econtext.config['on_start'](self.econtext)

        _profile_hook('main', self._dispatch_calls)


class ExternalContext(object):
    detached = False

    def __init__(self, config):
        self.config = config

    def _on_broker_exit(self):
        if not self.config['profiling']:
            os.kill(os.getpid(), signal.SIGTERM)

    def _service_stub_main(self, msg):
        import mitogen.service
        pool = mitogen.service.get_or_create_pool(router=self.router)
        pool._receiver._on_receive(msg)

    def _on_call_service_msg(self, msg):
        """
        Stub service handler. Start a thread to import the mitogen.service
        implementation from, and deliver the message to the newly constructed
        pool. This must be done as CALL_SERVICE for e.g. PushFileService may
        race with a CALL_FUNCTION blocking the main thread waiting for a result
        from that service.
        """
        if not msg.is_dead:
            th = threading.Thread(target=self._service_stub_main, args=(msg,))
            th.start()

    def _on_shutdown_msg(self, msg):
        _v and LOG.debug('_on_shutdown_msg(%r)', msg)
        if not msg.is_dead:
            self.broker.shutdown()

    def _on_parent_disconnect(self):
        if self.detached:
            mitogen.parent_ids = []
            mitogen.parent_id = None
            LOG.info('Detachment complete')
        else:
            _v and LOG.debug('%r: parent stream is gone, dying.', self)
            self.broker.shutdown()

    def detach(self):
        self.detached = True
        stream = self.router.stream_by_id(mitogen.parent_id)
        if stream:  # not double-detach()'d
            os.setsid()
            self.parent.send_await(Message(handle=DETACHING))
            LOG.info('Detaching from %r; parent is %s', stream, self.parent)
            for x in range(20):
                pending = self.broker.defer_sync(lambda: stream.pending_bytes())
                if not pending:
                    break
                time.sleep(0.05)
            if pending:
                LOG.error('Stream had %d bytes after 2000ms', pending)
            self.broker.defer(stream.on_disconnect, self.broker)

    def _setup_master(self):
        Router.max_message_size = self.config['max_message_size']
        if self.config['profiling']:
            enable_profiling()
        self.broker = Broker()
        self.router = Router(self.broker)
        self.router.debug = self.config.get('debug', False)
        self.router.undirectional = self.config['unidirectional']
        self.router.add_handler(
            fn=self._on_shutdown_msg,
            handle=SHUTDOWN,
            policy=has_parent_authority,
        )
        self.router.add_handler(
            fn=self._on_call_service_msg,
            handle=CALL_SERVICE,
            policy=has_parent_authority,
        )
        self.master = Context(self.router, 0, 'master')
        parent_id = self.config['parent_ids'][0]
        if parent_id == 0:
            self.parent = self.master
        else:
            self.parent = Context(self.router, parent_id, 'parent')

        in_fd = self.config.get('in_fd', 100)
        out_fd = self.config.get('out_fd', 1)
        self.stream = Stream(self.router, parent_id)
        self.stream.name = 'parent'
        self.stream.accept(in_fd, out_fd)
        self.stream.receive_side.keep_alive = False

        listen(self.stream, 'disconnect', self._on_parent_disconnect)
        listen(self.broker, 'exit', self._on_broker_exit)

        os.close(in_fd)

    def _reap_first_stage(self):
        try:
            os.wait()  # Reap first stage.
        except OSError:
            pass  # No first stage exists (e.g. fakessh)

    def _setup_logging(self):
        self.log_handler = LogHandler(self.master)
        root = logging.getLogger()
        root.setLevel(self.config['log_level'])
        root.handlers = [self.log_handler]
        if self.config['debug']:
            enable_debug_logging()

    def _setup_importer(self):
        importer = self.config.get('importer')
        if importer:
            importer._install_handler(self.router)
            importer._context = self.parent
        else:
            core_src_fd = self.config.get('core_src_fd', 101)
            if core_src_fd:
                fp = os.fdopen(core_src_fd, 'rb', 1)
                try:
                    core_src = fp.read()
                    # Strip "ExternalContext.main()" call from last line.
                    core_src = b('\n').join(core_src.splitlines()[:-1])
                finally:
                    fp.close()
            else:
                core_src = None

            importer = Importer(
                self.router,
                self.parent,
                core_src,
                self.config.get('whitelist', ()),
                self.config.get('blacklist', ()),
            )

        self.importer = importer
        self.router.importer = importer
        sys.meta_path.append(self.importer)

    def _setup_package(self):
        global mitogen
        mitogen = imp.new_module('mitogen')
        mitogen.__package__ = 'mitogen'
        mitogen.__path__ = []
        mitogen.__loader__ = self.importer
        mitogen.main = lambda *args, **kwargs: (lambda func: None)
        mitogen.core = sys.modules['__main__']
        mitogen.core.__file__ = 'x/mitogen/core.py'  # For inspect.getsource()
        mitogen.core.__loader__ = self.importer
        sys.modules['mitogen'] = mitogen
        sys.modules['mitogen.core'] = mitogen.core
        del sys.modules['__main__']

    def _setup_globals(self):
        mitogen.is_master = False
        mitogen.__version__ = self.config['version']
        mitogen.context_id = self.config['context_id']
        mitogen.parent_ids = self.config['parent_ids'][:]
        mitogen.parent_id = mitogen.parent_ids[0]

    def _setup_stdio(self):
        # We must open this prior to closing stdout, otherwise it will recycle
        # a standard handle, the dup2() will not error, and on closing it, we
        # lose a standrd handle, causing later code to again recycle a standard
        # handle.
        fp = open('/dev/null')

        # When sys.stdout was opened by the runtime, overwriting it will not
        # cause close to be called. However when forking from a child that
        # previously used fdopen, overwriting it /will/ cause close to be
        # called. So we must explicitly close it before IoLogger overwrites the
        # file descriptor, otherwise the assignment below will cause stdout to
        # be closed.
        sys.stdout.close()
        sys.stdout = None

        try:
            os.dup2(fp.fileno(), 0)
            os.dup2(fp.fileno(), 1)
            os.dup2(fp.fileno(), 2)
        finally:
            fp.close()

        self.stdout_log = IoLogger(self.broker, 'stdout', 1)
        self.stderr_log = IoLogger(self.broker, 'stderr', 2)
        # Reopen with line buffering.
        sys.stdout = os.fdopen(1, 'w', 1)

    def main(self):
        self._setup_master()
        try:
            try:
                self._setup_logging()
                self._setup_importer()
                self._reap_first_stage()
                if self.config.get('setup_package', True):
                    self._setup_package()
                self._setup_globals()
                if self.config.get('setup_stdio', True):
                    self._setup_stdio()

                self.dispatcher = Dispatcher(self)
                self.router.register(self.parent, self.stream)
                self.log_handler.uncork()

                sys.executable = os.environ.pop('ARGV0', sys.executable)
                _v and LOG.debug('Connected to %s; my ID is %r, PID is %r',
                                 self.parent, mitogen.context_id, os.getpid())
                _v and LOG.debug('Recovered sys.executable: %r', sys.executable)

                self.dispatcher.run()
                _v and LOG.debug('ExternalContext.main() normal exit')
            except KeyboardInterrupt:
                LOG.debug('KeyboardInterrupt received, exiting gracefully.')
            except BaseException:
                LOG.exception('ExternalContext.main() crashed')
                raise
        finally:
            self.broker.shutdown()
            self.broker.join()
