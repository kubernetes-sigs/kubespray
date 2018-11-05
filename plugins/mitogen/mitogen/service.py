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

import grp
import os
import os.path
import pprint
import pwd
import stat
import sys
import threading
import time

import mitogen.core
import mitogen.select
from mitogen.core import b
from mitogen.core import LOG


DEFAULT_POOL_SIZE = 16
_pool = None
_pool_pid = None
#: Serialize pool construction.
_pool_lock = threading.Lock()


if mitogen.core.PY3:
    def func_code(func):
        return func.__code__
else:
    def func_code(func):
        return func.func_code


@mitogen.core.takes_router
def get_or_create_pool(size=None, router=None):
    global _pool
    global _pool_pid
    _pool_lock.acquire()
    try:
        if _pool_pid != os.getpid():
            _pool = Pool(router, [], size=size or DEFAULT_POOL_SIZE)
            _pool_pid = os.getpid()
        return _pool
    finally:
        _pool_lock.release()


def validate_arg_spec(spec, args):
    for name in spec:
        try:
            obj = args[name]
        except KeyError:
            raise mitogen.core.CallError(
                'Required argument %r missing.' % (name,)
            )

        if not isinstance(obj, spec[name]):
            raise mitogen.core.CallError(
                'Argument %r type incorrect, got %r, expected %r' % (
                    name,
                    type(obj),
                    spec[name]
                )
            )


def arg_spec(spec):
    """
    Annotate a method as requiring arguments with a specific type. This only
    validates required arguments. For optional arguments, write a manual check
    within the function.

    ::

        @mitogen.service.arg_spec({
            'path': str
        })
        def fetch_path(self, path, optional=None):
            ...

    :param dict spec:
        Mapping from argument name to expected type.
    """
    def wrapper(func):
        func.mitogen_service__arg_spec = spec
        return func
    return wrapper


def expose(policy):
    """
    Annotate a method to permit access to contexts matching an authorization
    policy. The annotation may be specified multiple times. Methods lacking any
    authorization policy are not accessible.

    ::

        @mitogen.service.expose(policy=mitogen.service.AllowParents())
        def unsafe_operation(self):
            ...

    :param mitogen.service.Policy policy:
        The policy to require.
    """
    def wrapper(func):
        func.mitogen_service__policies = (
            [policy] +
            getattr(func, 'mitogen_service__policies', [])
        )
        return func
    return wrapper


def no_reply():
    """
    Annotate a method as one that does not generate a response. Messages sent
    by the method are done so explicitly. This can be used for fire-and-forget
    endpoints where the requestee never receives a reply.
    """
    def wrapper(func):
        func.mitogen_service__no_reply = True
        return func
    return wrapper


class Error(Exception):
    """
    Raised when an error occurs configuring a service or pool.
    """
    pass  # cope with minify_source() bug.


class Policy(object):
    """
    Base security policy.
    """
    def is_authorized(self, service, msg):
        raise NotImplementedError()


class AllowAny(Policy):
    def is_authorized(self, service, msg):
        return True


class AllowParents(Policy):
    def is_authorized(self, service, msg):
        return (msg.auth_id in mitogen.parent_ids or
                msg.auth_id == mitogen.context_id)


class Activator(object):
    """
    """
    def is_permitted(self, mod_name, class_name, msg):
        return mitogen.core.has_parent_authority(msg)

    not_active_msg = (
        'Service %r is not yet activated in this context, and the '
        'caller is not privileged, therefore autoactivation is disabled.'
    )

    def activate(self, pool, service_name, msg):
        mod_name, _, class_name = service_name.rpartition('.')
        if msg and not self.is_permitted(mod_name, class_name, msg):
            raise mitogen.core.CallError(self.not_active_msg, service_name)

        module = mitogen.core.import_module(mod_name)
        klass = getattr(module, class_name)
        service = klass(router=pool.router)
        pool.add(service)
        return service


class Invoker(object):
    def __init__(self, service):
        self.service = service

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.service)

    unauthorized_msg = (
        'Caller is not authorized to invoke %r of service %r'
    )

    def _validate(self, method_name, kwargs, msg):
        method = getattr(self.service, method_name, None)
        if method is None:
            raise mitogen.core.CallError('No such method: %r', method_name)

        policies = getattr(method, 'mitogen_service__policies', None)
        if not policies:
            raise mitogen.core.CallError('Method has no policies set.')

        if not all(p.is_authorized(self.service, msg) for p in policies):
            raise mitogen.core.CallError(
                self.unauthorized_msg,
                method_name,
                self.service.name()
            )

        required = getattr(method, 'mitogen_service__arg_spec', {})
        validate_arg_spec(required, kwargs)

    def _invoke(self, method_name, kwargs, msg):
        method = getattr(self.service, method_name)
        if 'msg' in func_code(method).co_varnames:
            kwargs['msg'] = msg  # TODO: hack

        no_reply = getattr(method, 'mitogen_service__no_reply', False)
        ret = None
        try:
            ret = method(**kwargs)
            if no_reply:
                return Service.NO_REPLY
            return ret
        except Exception:
            if no_reply:
                LOG.exception('While calling no-reply method %s.%s',
                              type(self.service).__name__,
                              method.func_name)
            else:
                raise

    def invoke(self, method_name, kwargs, msg):
        self._validate(method_name, kwargs, msg)
        response = self._invoke(method_name, kwargs, msg)
        if response is not Service.NO_REPLY:
            msg.reply(response)


class SerializedInvoker(Invoker):
    def __init__(self, **kwargs):
        super(SerializedInvoker, self).__init__(**kwargs)
        self._lock = threading.Lock()
        self._queue = []
        self._running = False

    def _pop(self):
        self._lock.acquire()
        try:
            try:
                return self._queue.pop(0)
            except IndexError:
                self._running = False
        finally:
            self._lock.release()

    def _run(self):
        while True:
            tup = self._pop()
            if tup is None:
                return
            method_name, kwargs, msg = tup
            try:
                super(SerializedInvoker, self).invoke(method_name, kwargs, msg)
            except mitogen.core.CallError:
                e = sys.exc_info()[1]
                LOG.warning('%r: call error: %s: %s', self, msg, e)
                msg.reply(e)
            except Exception:
                LOG.exception('%r: while invoking %s()', self, method_name)
                msg.reply(mitogen.core.Message.dead())

    def invoke(self, method_name, kwargs, msg):
        self._lock.acquire()
        try:
            self._queue.append((method_name, kwargs, msg))
            first = not self._running
            self._running = True
        finally:
            self._lock.release()

        if first:
            self._run()
        return Service.NO_REPLY


class DeduplicatingInvoker(Invoker):
    """
    A service that deduplicates and caches expensive responses. Requests are
    deduplicated according to a customizable key, and the single expensive
    response is broadcast to all requestors.

    A side effect of this class is that processing of the single response is
    always serialized according to the result of :py:meth:`key_from_request`.

    Only one pool thread is blocked during generation of the response,
    regardless of the number of requestors.
    """
    def __init__(self, service):
        super(DeduplicatingInvoker, self).__init__(service)
        self._responses = {}
        self._waiters = {}
        self._lock = threading.Lock()

    def key_from_request(self, method_name, kwargs):
        """
        Generate a deduplication key from the request. The default
        implementation returns a string based on a stable representation of the
        input dictionary generated by :py:func:`pprint.pformat`.
        """
        return pprint.pformat((method_name, kwargs))

    def get_response(self, args):
        raise NotImplementedError()

    def _produce_response(self, key, response):
        self._lock.acquire()
        try:
            assert key not in self._responses
            assert key in self._waiters
            self._responses[key] = response
            for msg in self._waiters.pop(key):
                msg.reply(response)
        finally:
            self._lock.release()

    def _invoke(self, method_name, kwargs, msg):
        key = self.key_from_request(method_name, kwargs)
        self._lock.acquire()
        try:
            if key in self._responses:
                return self._responses[key]

            if key in self._waiters:
                self._waiters[key].append(msg)
                return Service.NO_REPLY

            self._waiters[key] = [msg]
        finally:
            self._lock.release()

        # I'm the unlucky thread that must generate the response.
        try:
            response = getattr(self, method_name)(**kwargs)
            self._produce_response(key, response)
        except mitogen.core.CallError:
            e = sys.exc_info()[1]
            self._produce_response(key, e)
        except Exception:
            e = sys.exc_info()[1]
            self._produce_response(key, mitogen.core.CallError(e))

        return Service.NO_REPLY


class Service(object):
    #: Sentinel object to suppress reply generation, since returning
    #: :data:`None` will trigger a response message containing the pickled
    #: :data:`None`.
    NO_REPLY = object()

    invoker_class = Invoker

    @classmethod
    def name(cls):
        return u'%s.%s' % (cls.__module__, cls.__name__)

    def __init__(self, router):
        self.router = router
        self.select = mitogen.select.Select()

    def __repr__(self):
        return '%s()' % (self.__class__.__name__,)

    def on_message(self, recv, msg):
        """
        Called when a message arrives on any of :attr:`select`'s registered
        receivers.
        """

    def on_shutdown(self):
        """
        Called by Pool.shutdown() once the last worker thread has exitted.
        """


class Pool(object):
    """
    Manage a pool of at least one thread that will be used to process messages
    for a collection of services.

    Internally this is implemented by subscribing every :py:class:`Service`'s
    :py:class:`mitogen.core.Receiver` using a single
    :py:class:`mitogen.select.Select`, then arranging for every thread to
    consume messages delivered to that select.

    In this way the threads are fairly shared by all available services, and no
    resources are dedicated to a single idle service.

    There is no penalty for exposing large numbers of services; the list of
    exposed services could even be generated dynamically in response to your
    program's configuration or its input data.

    :param mitogen.core.Router router:
        Router to listen for ``CALL_SERVICE`` messages on.
    :param list services:
        Initial list of services to register.
    """
    activator_class = Activator

    def __init__(self, router, services, size=1):
        self.router = router
        self._activator = self.activator_class()
        self._receiver = mitogen.core.Receiver(
            router=router,
            handle=mitogen.core.CALL_SERVICE,
        )

        self._select = mitogen.select.Select(oneshot=False)
        self._select.add(self._receiver)
        #: Serialize service construction.
        self._lock = threading.Lock()
        self._func_by_recv = {self._receiver: self._on_service_call}
        self._invoker_by_name = {}

        for service in services:
            self.add(service)
        self._threads = []
        for x in range(size):
            name = 'mitogen.service.Pool.%x.worker-%d' % (id(self), x,)
            thread = threading.Thread(
                name=name,
                target=mitogen.core._profile_hook,
                args=(name, self._worker_main),
            )
            thread.start()
            self._threads.append(thread)

        LOG.debug('%r: initialized', self)

    @property
    def size(self):
        return len(self._threads)

    def add(self, service):
        name = service.name()
        if name in self._invoker_by_name:
            raise Error('service named %r already registered' % (name,))
        assert service.select not in self._func_by_recv
        invoker = service.invoker_class(service=service)
        self._invoker_by_name[name] = invoker
        self._func_by_recv[service.select] = service.on_message

    closed = False

    def stop(self, join=True):
        self.closed = True
        self._select.close()
        if join:
            self.join()

    def join(self):
        for th in self._threads:
            th.join()
        for invoker in self._invoker_by_name.values():
            invoker.service.on_shutdown()

    def get_invoker(self, name, msg):
        self._lock.acquire()
        try:
            invoker = self._invoker_by_name.get(name)
            if not invoker:
                service = self._activator.activate(self, name, msg)
                invoker = service.invoker_class(service=service)
                self._invoker_by_name[name] = invoker
        finally:
            self._lock.release()

        return invoker

    def get_service(self, name):
        invoker = self.get_invoker(name, None)
        return invoker.service

    def _validate(self, msg):
        tup = msg.unpickle(throw=False)
        if not (isinstance(tup, tuple) and
                len(tup) == 3 and
                isinstance(tup[0], mitogen.core.AnyTextType) and
                isinstance(tup[1], mitogen.core.AnyTextType) and
                isinstance(tup[2], dict)):
            raise mitogen.core.CallError('Invalid message format.')

    def _on_service_call(self, recv, msg):
        service_name = None
        method_name = None
        try:
            self._validate(msg)
            service_name, method_name, kwargs = msg.unpickle()
            invoker = self.get_invoker(service_name, msg)
            return invoker.invoke(method_name, kwargs, msg)
        except mitogen.core.CallError:
            e = sys.exc_info()[1]
            LOG.warning('%r: call error: %s: %s', self, msg, e)
            msg.reply(e)
        except Exception:
            LOG.exception('%r: while invoking %r of %r',
                          self, method_name, service_name)
            e = sys.exc_info()[1]
            msg.reply(mitogen.core.CallError(e))

    def _worker_run(self):
        while not self.closed:
            try:
                msg = self._select.get()
            except (mitogen.core.ChannelError, mitogen.core.LatchError):
                e = sys.exc_info()[1]
                LOG.info('%r: channel or latch closed, exitting: %s', self, e)
                return

            func = self._func_by_recv[msg.receiver]
            try:
                func(msg.receiver, msg)
            except Exception:
                LOG.exception('While handling %r using %r', msg, func)

    def _worker_main(self):
        try:
            self._worker_run()
        except Exception:
            th = threading.currentThread()
            LOG.exception('%r: worker %r crashed', self, th.name)
            raise

    def __repr__(self):
        th = threading.currentThread()
        return 'mitogen.service.Pool(%#x, size=%d, th=%r)' % (
            id(self),
            len(self._threads),
            th.name,
        )


class FileStreamState(object):
    def __init__(self):
        #: List of [(Sender, file object)]
        self.jobs = []
        self.completing = {}
        #: In-flight byte count.
        self.unacked = 0
        #: Lock.
        self.lock = threading.Lock()


class PushFileService(Service):
    """
    Push-based file service. Files are delivered and cached in RAM, sent
    recursively from parent to child. A child that requests a file via
    :meth:`get` will block until it has ben delivered by a parent.

    This service will eventually be merged into FileService.
    """
    invoker_class = SerializedInvoker

    def __init__(self, **kwargs):
        super(PushFileService, self).__init__(**kwargs)
        self._lock = threading.Lock()
        self._cache = {}
        self._waiters = {}
        self._sent_by_stream = {}

    def get(self, path):
        self._lock.acquire()
        try:
            if path in self._cache:
                return self._cache[path]
            waiters = self._waiters.setdefault(path, [])
            latch = mitogen.core.Latch()
            waiters.append(lambda: latch.put(None))
        finally:
            self._lock.release()

        LOG.debug('%r.get(%r) waiting for uncached file to arrive', self, path)
        latch.get()
        LOG.debug('%r.get(%r) -> %r', self, path, self._cache[path])
        return self._cache[path]

    def _forward(self, context, path):
        stream = self.router.stream_by_id(context.context_id)
        child = mitogen.core.Context(self.router, stream.remote_id)
        sent = self._sent_by_stream.setdefault(stream, set())
        if path in sent and child.context_id != context.context_id:
            child.call_service_async(
                service_name=self.name(),
                method_name='forward',
                path=path,
                context=context
            ).close()
        else:
            child.call_service_async(
                service_name=self.name(),
                method_name='store_and_forward',
                path=path,
                data=self._cache[path],
                context=context
            ).close()

    @expose(policy=AllowParents())
    @arg_spec({
        'context': mitogen.core.Context,
        'paths': list,
        'modules': list,
    })
    def propagate_paths_and_modules(self, context, paths, modules):
        """
        One size fits all method to ensure a target context has been preloaded
        with a set of small files and Python modules.
        """
        for path in paths:
            self.propagate_to(context, path)
        self.router.responder.forward_modules(context, modules)

    @expose(policy=AllowParents())
    @arg_spec({
        'context': mitogen.core.Context,
        'path': mitogen.core.FsPathTypes,
    })
    def propagate_to(self, context, path):
        LOG.debug('%r.propagate_to(%r, %r)', self, context, path)
        if path not in self._cache:
            fp = open(path, 'rb')
            try:
                self._cache[path] = mitogen.core.Blob(fp.read())
            finally:
                fp.close()
        self._forward(context, path)

    def _store(self, path, data):
        self._lock.acquire()
        try:
            self._cache[path] = data
            return self._waiters.pop(path, [])
        finally:
            self._lock.release()

    @expose(policy=AllowParents())
    @no_reply()
    @arg_spec({
        'path': mitogen.core.FsPathTypes,
        'data': mitogen.core.Blob,
        'context': mitogen.core.Context,
    })
    def store_and_forward(self, path, data, context):
        LOG.debug('%r.store_and_forward(%r, %r, %r)',
                  self, path, data, context)
        waiters = self._store(path, data)
        if context.context_id != mitogen.context_id:
            self._forward(context, path)
        for callback in waiters:
            callback()

    @expose(policy=AllowParents())
    @no_reply()
    @arg_spec({
        'path': mitogen.core.FsPathTypes,
        'context': mitogen.core.Context,
    })
    def forward(self, path, context):
        LOG.debug('%r.forward(%r, %r)', self, path, context)
        if path not in self._cache:
            LOG.error('%r: %r is not in local cache', self, path)
            return
        self._forward(path, context)


class FileService(Service):
    """
    Streaming file server, used to serve small and huge files alike. Paths must
    be registered by a trusted context before they will be served to a child.

    Transfers are divided among the physical streams that connect external
    contexts, ensuring each stream never has excessive data buffered in RAM,
    while still maintaining enough to fully utilize available bandwidth. This
    is achieved by making an initial bandwidth assumption, enqueueing enough
    chunks to fill that assumed pipe, then responding to delivery
    acknowledgements from the receiver by scheduling new chunks.

    Transfers proceed one-at-a-time per stream. When multiple contexts exist on
    a stream (e.g. one is the SSH account, another is a sudo account, and a
    third is a proxied SSH connection), each request is satisfied in turn
    before subsequent requests start flowing. This ensures when a stream is
    contended, priority is given to completing individual transfers rather than
    potentially aborting many partial transfers, causing the bandwidth to be
    wasted.

    Theory of operation:
        1. Trusted context (i.e. WorkerProcess) calls register(), making a
           file available to any untrusted context.
        2. Requestee context creates a mitogen.core.Receiver() to receive
           chunks, then calls fetch(path, recv.to_sender()), to set up the
           transfer.
        3. fetch() replies to the call with the file's metadata, then
           schedules an initial burst up to the window size limit (1MiB).
        4. Chunks begin to arrive in the requestee, which calls acknowledge()
           for each 128KiB received.
        5. The acknowledge() call arrives at FileService, which scheduled a new
           chunk to refill the drained window back to the size limit.
        6. When the last chunk has been pumped for a single transfer,
           Sender.close() is called causing the receive loop in
           target.py::_get_file() to exit, allowing that code to compare the
           transferred size with the total file size from the metadata.
        7. If the sizes mismatch, _get_file()'s caller is informed which will
           discard the result and log/raise an error.

    Shutdown:
        1. process.py calls service.Pool.shutdown(), which arranges for the
           service pool threads to exit and be joined, guranteeing no new
           requests can arrive, before calling Service.on_shutdown() for each
           registered service.
        2. FileService.on_shutdown() walks every in-progress transfer and calls
           Sender.close(), causing Receiver loops in the requestees to exit
           early. The size check fails and any partially downloaded file is
           discarded.
        3. Control exits _get_file() in every target, and graceful shutdown can
           proceed normally, without the associated thread needing to be
           forcefully killed.
    """
    unregistered_msg = 'Path is not registered with FileService.'
    context_mismatch_msg = 'sender= kwarg context must match requestee context'

    #: Burst size. With 1MiB and 10ms RTT max throughput is 100MiB/sec, which
    #: is 5x what SSH can handle on a 2011 era 2.4Ghz Core i5.
    window_size_bytes = 1048576

    def __init__(self, router):
        super(FileService, self).__init__(router)
        #: Mapping of registered path -> file size.
        self._metadata_by_path = {}
        #: Mapping of Stream->FileStreamState.
        self._state_by_stream = {}

    def _name_or_none(self, func, n, attr):
        try:
            return getattr(func(n), attr)
        except KeyError:
            return None

    @expose(policy=AllowParents())
    @arg_spec({
        'path': mitogen.core.FsPathTypes,
    })
    def register(self, path):
        """
        Authorize a path for access by children. Repeat calls with the same
        path is harmless.

        :param str path:
            File path.
        """
        if path in self._metadata_by_path:
            return

        st = os.stat(path)
        if not stat.S_ISREG(st.st_mode):
            raise IOError('%r is not a regular file.' % (path,))

        LOG.debug('%r: registering %r', self, path)
        self._metadata_by_path[path] = {
            'size': st.st_size,
            'mode': st.st_mode,
            'owner': self._name_or_none(pwd.getpwuid, 0, 'pw_name'),
            'group': self._name_or_none(grp.getgrgid, 0, 'gr_name'),
            'mtime': st.st_mtime,
            'atime': st.st_atime,
        }

    def on_shutdown(self):
        """
        Respond to shutdown by sending close() to every target, allowing their
        receive loop to exit and clean up gracefully.
        """
        LOG.debug('%r.on_shutdown()', self)
        for stream, state in self._state_by_stream.items():
            state.lock.acquire()
            try:
                for sender, fp in reversed(state.jobs):
                    sender.close()
                    fp.close()
                    state.jobs.pop()
            finally:
                state.lock.release()

    # The IO loop pumps 128KiB chunks. An ideal message is a multiple of this,
    # odd-sized messages waste one tiny write() per message on the trailer.
    # Therefore subtract 10 bytes pickle overhead + 24 bytes header.
    IO_SIZE = mitogen.core.CHUNK_SIZE - (mitogen.core.Stream.HEADER_LEN + (
        len(
            mitogen.core.Message.pickled(
                mitogen.core.Blob(b(' ') * mitogen.core.CHUNK_SIZE)
            ).data
        ) - mitogen.core.CHUNK_SIZE
    ))

    def _schedule_pending_unlocked(self, state):
        """
        Consider the pending transfers for a stream, pumping new chunks while
        the unacknowledged byte count is below :attr:`window_size_bytes`. Must
        be called with the FileStreamState lock held.

        :param FileStreamState state:
            Stream to schedule chunks for.
        """
        while state.jobs and state.unacked < self.window_size_bytes:
            sender, fp = state.jobs[0]
            s = fp.read(self.IO_SIZE)
            if s:
                state.unacked += len(s)
                sender.send(mitogen.core.Blob(s))
            else:
                # File is done. Cause the target's receive loop to exit by
                # closing the sender, close the file, and remove the job entry.
                sender.close()
                fp.close()
                state.jobs.pop(0)

    @expose(policy=AllowAny())
    @no_reply()
    @arg_spec({
        'path': mitogen.core.FsPathTypes,
        'sender': mitogen.core.Sender,
    })
    def fetch(self, path, sender, msg):
        """
        Start a transfer for a registered path.

        :param str path:
            File path.
        :param mitogen.core.Sender sender:
            Sender to receive file data.
        :returns:
            Dict containing the file metadata:

            * ``size``: File size in bytes.
            * ``mode``: Integer file mode.
            * ``owner``: Owner account name on host machine.
            * ``group``: Owner group name on host machine.
            * ``mtime``: Floating point modification time.
            * ``ctime``: Floating point change time.
        :raises Error:
            Unregistered path, or Sender did not match requestee context.
        """
        if path not in self._metadata_by_path:
            raise Error(self.unregistered_msg)
        if msg.src_id != sender.context.context_id:
            raise Error(self.context_mismatch_msg)

        LOG.debug('Serving %r', path)
        try:
            fp = open(path, 'rb', self.IO_SIZE)
        except IOError:
            msg.reply(mitogen.core.CallError(
                sys.exc_info()[1]
            ))
            return

        # Response must arrive first so requestee can begin receive loop,
        # otherwise first ack won't arrive until all pending chunks were
        # delivered. In that case max BDP would always be 128KiB, aka. max
        # ~10Mbit/sec over a 100ms link.
        msg.reply(self._metadata_by_path[path])

        stream = self.router.stream_by_id(sender.context.context_id)
        state = self._state_by_stream.setdefault(stream, FileStreamState())
        state.lock.acquire()
        try:
            state.jobs.append((sender, fp))
            self._schedule_pending_unlocked(state)
        finally:
            state.lock.release()

    @expose(policy=AllowAny())
    @no_reply()
    @arg_spec({
        'size': int,
    })
    @no_reply()
    def acknowledge(self, size, msg):
        """
        Acknowledge bytes received by a transfer target, scheduling new chunks
        to keep the window full. This should be called for every chunk received
        by the target.
        """
        stream = self.router.stream_by_id(msg.src_id)
        state = self._state_by_stream[stream]
        state.lock.acquire()
        try:
            if state.unacked < size:
                LOG.error('%r.acknowledge(src_id %d): unacked=%d < size %d',
                          self, msg.src_id, state.unacked, size)
            state.unacked -= min(state.unacked, size)
            self._schedule_pending_unlocked(state)
        finally:
            state.lock.release()

    @classmethod
    def get(cls, context, path, out_fp):
        """
        Streamily download a file from the connection multiplexer process in
        the controller.

        :param mitogen.core.Context context:
            Reference to the context hosting the FileService that will be used
            to fetch the file.
        :param bytes path:
            FileService registered name of the input file.
        :param bytes out_path:
            Name of the output path on the local disk.
        :returns:
            :data:`True` on success, or :data:`False` if the transfer was
            interrupted and the output should be discarded.
        """
        LOG.debug('get_file(): fetching %r from %r', path, context)
        t0 = time.time()
        recv = mitogen.core.Receiver(router=context.router)
        metadata = context.call_service(
            service_name=cls.name(),
            method_name='fetch',
            path=path,
            sender=recv.to_sender(),
        )

        for chunk in recv:
            s = chunk.unpickle()
            LOG.debug('get_file(%r): received %d bytes', path, len(s))
            context.call_service_async(
                service_name=cls.name(),
                method_name='acknowledge',
                size=len(s),
            ).close()
            out_fp.write(s)

        ok = out_fp.tell() == metadata['size']
        if not ok:
            LOG.error('get_file(%r): receiver was closed early, controller '
                      'is likely shutting down.', path)

        LOG.debug('target.get_file(): fetched %d bytes of %r from %r in %dms',
                  metadata['size'], path, context, 1000 * (time.time() - t0))
        return ok, metadata
