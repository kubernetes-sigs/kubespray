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
Classes in this file define Mitogen 'services' that run (initially) within the
connection multiplexer process that is forked off the top-level controller
process.

Once a worker process connects to a multiplexer process
(Connection._connect()), it communicates with these services to establish new
connections, grant access to files by children, and register for notification
when a child has completed a job.
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import os
import os.path
import sys
import threading

import ansible.constants

import mitogen
import mitogen.service
import mitogen.utils
import ansible_mitogen.loaders
import ansible_mitogen.module_finder
import ansible_mitogen.target


LOG = logging.getLogger(__name__)

# Force load of plugin to ensure ConfigManager has definitions loaded. Done
# during module import to ensure a single-threaded environment; PluginLoader
# is not thread-safe.
ansible_mitogen.loaders.shell_loader.get('sh')


if sys.version_info[0] == 3:
    def reraise(tp, value, tb):
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value
else:
    exec(
        "def reraise(tp, value, tb=None):\n"
        "    raise tp, value, tb\n"
     )


def _get_candidate_temp_dirs():
    options = ansible.constants.config.get_plugin_options('shell', 'sh')

    # Pre 2.5 this came from ansible.constants.
    remote_tmp = (options.get('remote_tmp') or
                  ansible.constants.DEFAULT_REMOTE_TMP)
    dirs = list(options.get('system_tmpdirs', ('/var/tmp', '/tmp')))
    dirs.insert(0, remote_tmp)
    return mitogen.utils.cast(dirs)


def key_from_dict(**kwargs):
    """
    Return a unique string representation of a dict as quickly as possible.
    Used to generated deduplication keys from a request.
    """
    out = []
    stack = [kwargs]
    while stack:
        obj = stack.pop()
        if isinstance(obj, dict):
            stack.extend(sorted(obj.items()))
        elif isinstance(obj, (list, tuple)):
            stack.extend(obj)
        else:
            out.append(str(obj))
    return ''.join(out)


class Error(Exception):
    pass


class ContextService(mitogen.service.Service):
    """
    Used by workers to fetch the single Context instance corresponding to a
    connection configuration, creating the matching connection if it does not
    exist.

    For connection methods and their parameters, see:
        https://mitogen.readthedocs.io/en/latest/api.html#context-factories

    This concentrates connections in the top-level process, which may become a
    bottleneck. The bottleneck can be removed using per-CPU connection
    processes and arranging for the worker to select one according to a hash of
    the connection parameters (sharding).
    """
    max_interpreters = int(os.getenv('MITOGEN_MAX_INTERPRETERS', '20'))

    def __init__(self, *args, **kwargs):
        super(ContextService, self).__init__(*args, **kwargs)
        self._lock = threading.Lock()
        #: Records the :meth:`get` result dict for successful calls, returned
        #: for identical subsequent calls. Keyed by :meth:`key_from_dict`.
        self._response_by_key = {}
        #: List of :class:`mitogen.core.Latch` awaiting the result for a
        #: particular key.
        self._latches_by_key = {}
        #: Mapping of :class:`mitogen.core.Context` -> reference count. Each
        #: call to :meth:`get` increases this by one. Calls to :meth:`put`
        #: decrease it by one.
        self._refs_by_context = {}
        #: List of contexts in creation order by via= parameter. When
        #: :attr:`max_interpreters` is reached, the most recently used context
        #: is destroyed to make room for any additional context.
        self._lru_by_via = {}
        #: :func:`key_from_dict` result by Context.
        self._key_by_context = {}
        #: Mapping of Context -> parent Context
        self._via_by_context = {}

    @mitogen.service.expose(mitogen.service.AllowParents())
    @mitogen.service.arg_spec({
        'context': mitogen.core.Context
    })
    def reset(self, context):
        """
        Return a reference, forcing close and discard of the underlying
        connection. Used for 'meta: reset_connection' or when some other error
        is detected.
        """
        LOG.debug('%r.reset(%r)', self, context)
        self._lock.acquire()
        try:
            self._shutdown_unlocked(context)
        finally:
            self._lock.release()

    @mitogen.service.expose(mitogen.service.AllowParents())
    @mitogen.service.arg_spec({
        'context': mitogen.core.Context
    })
    def put(self, context):
        """
        Return a reference, making it eligable for recycling once its reference
        count reaches zero.
        """
        LOG.debug('%r.put(%r)', self, context)
        self._lock.acquire()
        try:
            if self._refs_by_context.get(context, 0) == 0:
                LOG.warning('%r.put(%r): refcount was 0. shutdown_all called?',
                            self, context)
                return
            self._refs_by_context[context] -= 1
        finally:
            self._lock.release()

    def _produce_response(self, key, response):
        """
        Reply to every waiting request matching a configuration key with a
        response dictionary, deleting the list of waiters when done.

        :param str key:
            Result of :meth:`key_from_dict`
        :param dict response:
            Response dictionary
        :returns:
            Number of waiters that were replied to.
        """
        self._lock.acquire()
        try:
            latches = self._latches_by_key.pop(key)
            count = len(latches)
            for latch in latches:
                latch.put(response)
        finally:
            self._lock.release()
        return count

    def _forget_context_unlocked(self, context):
        key = self._key_by_context.get(context)
        if key is None:
            LOG.debug('%r: attempt to forget unknown %r', self, context)
            return

        self._response_by_key.pop(key, None)
        self._latches_by_key.pop(key, None)
        self._key_by_context.pop(context, None)
        self._refs_by_context.pop(context, None)
        self._via_by_context.pop(context, None)
        self._lru_by_via.pop(context, None)

    def _shutdown_unlocked(self, context, lru=None, new_context=None):
        """
        Arrange for `context` to be shut down, and optionally add `new_context`
        to the LRU list while holding the lock.
        """
        LOG.info('%r._shutdown_unlocked(): shutting down %r', self, context)
        context.shutdown()
        via = self._via_by_context.get(context)
        if via:
            lru = self._lru_by_via.get(via)
            if lru:
                if context in lru:
                    lru.remove(context)
                if new_context:
                    lru.append(new_context)
        self._forget_context_unlocked(context)

    def _update_lru_unlocked(self, new_context, spec, via):
        """
        Update the LRU ("MRU"?) list associated with the connection described
        by `kwargs`, destroying the most recently created context if the list
        is full. Finally add `new_context` to the list.
        """
        lru = self._lru_by_via.setdefault(via, [])
        if len(lru) < self.max_interpreters:
            lru.append(new_context)
            return

        for context in reversed(lru):
            if self._refs_by_context[context] == 0:
                break
        else:
            LOG.warning('via=%r reached maximum number of interpreters, '
                        'but they are all marked as in-use.', via)
            return

        self._via_by_context[new_context] = via
        self._shutdown_unlocked(context, lru=lru, new_context=new_context)

    def _update_lru(self, new_context, spec, via):
        self._lock.acquire()
        try:
            self._update_lru_unlocked(new_context, spec, via)
        finally:
            self._lock.release()

    @mitogen.service.expose(mitogen.service.AllowParents())
    def shutdown_all(self):
        """
        For testing use, arrange for all connections to be shut down.
        """
        self._lock.acquire()
        try:
            for context in list(self._key_by_context):
                self._shutdown_unlocked(context)
        finally:
            self._lock.release()

    def _on_stream_disconnect(self, stream):
        """
        Respond to Stream disconnection by deleting any record of contexts
        reached via that stream. This method runs in the Broker thread and must
        not to block.
        """
        # TODO: there is a race between creation of a context and disconnection
        # of its related stream. An error reply should be sent to any message
        # in _latches_by_key below.
        self._lock.acquire()
        try:
            routes = self.router.route_monitor.get_routes(stream)
            for context in list(self._key_by_context):
                if context.context_id in routes:
                    LOG.info('Dropping %r due to disconnect of %r',
                             context, stream)
                    self._forget_context_unlocked(context)
        finally:
            self._lock.release()

    ALWAYS_PRELOAD = (
        'ansible.module_utils.basic',
        'ansible.module_utils.json_utils',
        'ansible.release',
        'ansible_mitogen.runner',
        'ansible_mitogen.target',
        'mitogen.fork',
        'mitogen.service',
    )

    def _send_module_forwards(self, context):
        self.router.responder.forward_modules(context, self.ALWAYS_PRELOAD)

    _candidate_temp_dirs = None

    def _get_candidate_temp_dirs(self):
        """
        Return a list of locations to try to create the single temporary
        directory used by the run. This simply caches the (expensive) plugin
        load of :func:`_get_candidate_temp_dirs`.
        """
        if self._candidate_temp_dirs is None:
            self._candidate_temp_dirs = _get_candidate_temp_dirs()
        return self._candidate_temp_dirs

    def _connect(self, key, spec, via=None):
        """
        Actual connect implementation. Arranges for the Mitogen connection to
        be created and enqueues an asynchronous call to start the forked task
        parent in the remote context.

        :param key:
            Deduplication key representing the connection configuration.
        :param spec:
            Connection specification.
        :returns:
            Dict like::

                {
                    'context': mitogen.core.Context or None,
                    'via': mitogen.core.Context or None,
                    'init_child_result': {
                        'fork_context': mitogen.core.Context,
                        'home_dir': str or None,
                    },
                    'msg': str or None
                }

            Where `context` is a reference to the newly constructed context,
            `init_child_result` is the result of executing
            :func:`ansible_mitogen.target.init_child` in that context, `msg` is
            an error message and the remaining fields are :data:`None`, or
            `msg` is :data:`None` and the remaining fields are set.
        """
        try:
            method = getattr(self.router, spec['method'])
        except AttributeError:
            raise Error('unsupported method: %(transport)s' % spec)

        context = method(via=via, unidirectional=True, **spec['kwargs'])
        if via and spec.get('enable_lru'):
            self._update_lru(context, spec, via)
        else:
            # For directly connected contexts, listen to the associated
            # Stream's disconnect event and use it to invalidate dependent
            # Contexts.
            stream = self.router.stream_by_id(context.context_id)
            mitogen.core.listen(stream, 'disconnect',
                                lambda: self._on_stream_disconnect(stream))

        self._send_module_forwards(context)
        init_child_result = context.call(
            ansible_mitogen.target.init_child,
            log_level=LOG.getEffectiveLevel(),
            candidate_temp_dirs=self._get_candidate_temp_dirs(),
        )

        if os.environ.get('MITOGEN_DUMP_THREAD_STACKS'):
            from mitogen import debug
            context.call(debug.dump_to_logger)

        self._key_by_context[context] = key
        self._refs_by_context[context] = 0
        return {
            'context': context,
            'via': via,
            'init_child_result': init_child_result,
            'msg': None,
        }

    def _wait_or_start(self, spec, via=None):
        latch = mitogen.core.Latch()
        key = key_from_dict(via=via, **spec)
        self._lock.acquire()
        try:
            response = self._response_by_key.get(key)
            if response is not None:
                self._refs_by_context[response['context']] += 1
                latch.put(response)
                return latch

            latches = self._latches_by_key.setdefault(key, [])
            first = len(latches) == 0
            latches.append(latch)
        finally:
            self._lock.release()

        if first:
            # I'm the first requestee, so I will create the connection.
            try:
                response = self._connect(key, spec, via=via)
                count = self._produce_response(key, response)
                # Only record the response for non-error results.
                self._response_by_key[key] = response
                # Set the reference count to the number of waiters.
                self._refs_by_context[response['context']] += count
            except Exception:
                self._produce_response(key, sys.exc_info())

        return latch

    disconnect_msg = (
        'Channel was disconnected while connection attempt was in progress; '
        'this may be caused by an abnormal Ansible exit, or due to an '
        'unreliable target.'
    )

    @mitogen.service.expose(mitogen.service.AllowParents())
    @mitogen.service.arg_spec({
        'stack': list
    })
    def get(self, msg, stack):
        """
        Return a Context referring to an established connection with the given
        configuration, establishing new connections as necessary.

        :param list stack:
            Connection descriptions. Each element is a dict containing 'method'
            and 'kwargs' keys describing the Router method and arguments.
            Subsequent elements are proxied via the previous.

        :returns dict:
            * context: mitogen.parent.Context or None.
            * init_child_result: Result of :func:`init_child`.
            * msg: StreamError exception text or None.
            * method_name: string failing method name.
        """
        via = None
        for spec in stack:
            try:
                result = self._wait_or_start(spec, via=via).get()
                if isinstance(result, tuple):  # exc_info()
                    reraise(*result)
                via = result['context']
            except mitogen.core.ChannelError:
                return {
                    'context': None,
                    'init_child_result': None,
                    'method_name': spec['method'],
                    'msg': self.disconnect_msg,
                }
            except mitogen.core.StreamError as e:
                return {
                    'context': None,
                    'init_child_result': None,
                    'method_name': spec['method'],
                    'msg': str(e),
                }

        return result


class ModuleDepService(mitogen.service.Service):
    """
    Scan a new-style module and produce a cached mapping of module_utils names
    to their resolved filesystem paths.
    """
    invoker_class = mitogen.service.SerializedInvoker

    def __init__(self, *args, **kwargs):
        super(ModuleDepService, self).__init__(*args, **kwargs)
        self._cache = {}

    def _get_builtin_names(self, builtin_path, resolved):
        return [
            fullname
            for fullname, path, is_pkg in resolved
            if os.path.abspath(path).startswith(builtin_path)
        ]

    def _get_custom_tups(self, builtin_path, resolved):
        return [
            (fullname, path, is_pkg)
            for fullname, path, is_pkg in resolved
            if not os.path.abspath(path).startswith(builtin_path)
        ]

    @mitogen.service.expose(policy=mitogen.service.AllowParents())
    @mitogen.service.arg_spec({
        'module_name': mitogen.core.UnicodeType,
        'module_path': mitogen.core.FsPathTypes,
        'search_path': tuple,
        'builtin_path': mitogen.core.FsPathTypes,
        'context': mitogen.core.Context,
    })
    def scan(self, module_name, module_path, search_path, builtin_path, context):
        key = (module_name, search_path)
        if key not in self._cache:
            resolved = ansible_mitogen.module_finder.scan(
                module_name=module_name,
                module_path=module_path,
                search_path=tuple(search_path) + (builtin_path,),
            )
            builtin_path = os.path.abspath(builtin_path)
            builtin = self._get_builtin_names(builtin_path, resolved)
            custom = self._get_custom_tups(builtin_path, resolved)
            self._cache[key] = {
                'builtin': builtin,
                'custom': custom,
            }
        return self._cache[key]
