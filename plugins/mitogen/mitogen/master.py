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
This module implements functionality required by master processes, such as
starting new contexts via SSH. Its size is also restricted, since it must
be sent to any context that will be used to establish additional child
contexts.
"""

import dis
import imp
import inspect
import itertools
import logging
import os
import pkgutil
import re
import string
import sys
import threading
import types
import zlib

if not hasattr(pkgutil, 'find_loader'):
    # find_loader() was new in >=2.5, but the modern pkgutil.py syntax has
    # been kept intentionally 2.3 compatible so we can reuse it.
    from mitogen.compat import pkgutil

import mitogen
import mitogen.core
import mitogen.minify
import mitogen.parent

from mitogen.core import b
from mitogen.core import to_text
from mitogen.core import LOG
from mitogen.core import IOLOG

imap = getattr(itertools, 'imap', map)
izip = getattr(itertools, 'izip', zip)


RLOG = logging.getLogger('mitogen.ctx')


def _stdlib_paths():
    """Return a set of paths from which Python imports the standard library.
    """
    attr_candidates = [
        'prefix',
        'real_prefix',  # virtualenv: only set inside a virtual environment.
        'base_prefix',  # venv: always set, equal to prefix if outside.
    ]
    prefixes = (getattr(sys, a) for a in attr_candidates if hasattr(sys, a))
    version = 'python%s.%s' % sys.version_info[0:2]
    return set(os.path.abspath(os.path.join(p, 'lib', version))
               for p in prefixes)


def is_stdlib_name(modname):
    """Return :data:`True` if `modname` appears to come from the standard
    library.
    """
    if imp.is_builtin(modname) != 0:
        return True

    module = sys.modules.get(modname)
    if module is None:
        return False

    # six installs crap with no __file__
    modpath = os.path.abspath(getattr(module, '__file__', ''))
    return is_stdlib_path(modpath)


_STDLIB_PATHS = _stdlib_paths()


def is_stdlib_path(path):
    return any(
        os.path.commonprefix((libpath, path)) == libpath
        and 'site-packages' not in path
        and 'dist-packages' not in path
        for libpath in _STDLIB_PATHS
    )


def get_child_modules(path):
    """Return the suffixes of submodules directly neated beneath of the package
    directory at `path`.

    :param str path:
        Path to the module's source code on disk, or some PEP-302-recognized
        equivalent. Usually this is the module's ``__file__`` attribute, but
        is specified explicitly to avoid loading the module.

    :return:
        List of submodule name suffixes.
    """
    it = pkgutil.iter_modules([os.path.dirname(path)])
    return [to_text(name) for _, name, _ in it]


def get_core_source():
    """
    Master version of parent.get_core_source().
    """
    source = inspect.getsource(mitogen.core)
    return mitogen.minify.minimize_source(source)


if mitogen.is_master:
    # TODO: find a less surprising way of installing this.
    mitogen.parent.get_core_source = get_core_source


LOAD_CONST = dis.opname.index('LOAD_CONST')
IMPORT_NAME = dis.opname.index('IMPORT_NAME')


if sys.version_info < (3, 0):
    def iter_opcodes(co):
        # Yield `(op, oparg)` tuples from the code object `co`.
        ordit = imap(ord, co.co_code)
        nextb = ordit.next
        return ((c, (None
                     if c < dis.HAVE_ARGUMENT else
                     (nextb() | (nextb() << 8))))
                    for c in ordit)
elif sys.version_info < (3, 6):
    def iter_opcodes(co):
        # Yield `(op, oparg)` tuples from the code object `co`.
        ordit = iter(co.co_code)
        nextb = ordit.__next__
        return ((c, (None
                     if c < dis.HAVE_ARGUMENT else
                     (nextb() | (nextb() << 8))))
                    for c in ordit)
else:
    def iter_opcodes(co):
        # Yield `(op, oparg)` tuples from the code object `co`.
        ordit = iter(co.co_code)
        nextb = ordit.__next__
        # https://github.com/abarnert/cpython/blob/c095a32f/Python/wordcode.md
        return ((c, nextb()) for c in ordit)


def scan_code_imports(co):
    """Given a code object `co`, scan its bytecode yielding any
    ``IMPORT_NAME`` and associated prior ``LOAD_CONST`` instructions
    representing an `Import` statement or `ImportFrom` statement.

    :return:
        Generator producing `(level, modname, namelist)` tuples, where:

        * `level`: -1 for normal import, 0, for absolute import, and >0 for
          relative import.
        * `modname`: Name of module to import, or from where `namelist` names
          are imported.
        * `namelist`: for `ImportFrom`, the list of names to be imported from
          `modname`.
    """
    opit = iter_opcodes(co)
    opit, opit2, opit3 = itertools.tee(opit, 3)
    try:
        next(opit2)
        next(opit3)
        next(opit3)
    except StopIteration:
        return

    for oparg1, oparg2, (op3, arg3) in izip(opit, opit2, opit3):
        if op3 == IMPORT_NAME:
            op2, arg2 = oparg2
            op1, arg1 = oparg1
            if op1 == op2 == LOAD_CONST:
                yield (co.co_consts[arg1],
                       co.co_names[arg3],
                       co.co_consts[arg2] or ())


class ThreadWatcher(object):
    """
    Manage threads that wait for another thread to shut down, before invoking
    `on_join()` for each associated ThreadWatcher.

    In CPython it seems possible to use this method to ensure a non-main thread
    is signalled when the main thread has exited, using a third thread as a
    proxy.
    """
    #: Protects remaining _cls_* members.
    _cls_lock = threading.Lock()

    #: PID of the process that last modified the class data. If the PID
    #: changes, it means the thread watch dict refers to threads that no longer
    #: exist in the current process (since it forked), and so must be reset.
    _cls_pid = None

    #: Map watched Thread -> list of ThreadWatcher instances.
    _cls_instances_by_target = {}

    #: Map watched Thread -> watcher Thread for each watched thread.
    _cls_thread_by_target = {}

    @classmethod
    def _reset(cls):
        """If we have forked since the watch dictionaries were initialized, all
        that has is garbage, so clear it."""
        if os.getpid() != cls._cls_pid:
            cls._cls_pid = os.getpid()
            cls._cls_instances_by_target.clear()
            cls._cls_thread_by_target.clear()

    def __init__(self, target, on_join):
        self.target = target
        self.on_join = on_join

    @classmethod
    def _watch(cls, target):
        target.join()
        for watcher in cls._cls_instances_by_target[target]:
            watcher.on_join()

    def install(self):
        self._cls_lock.acquire()
        try:
            self._reset()
            lst = self._cls_instances_by_target.setdefault(self.target, [])
            lst.append(self)
            if self.target not in self._cls_thread_by_target:
                self._cls_thread_by_target[self.target] = threading.Thread(
                    name='mitogen.master.join_thread_async',
                    target=self._watch,
                    args=(self.target,)
                )
                self._cls_thread_by_target[self.target].start()
        finally:
            self._cls_lock.release()

    def remove(self):
        self._cls_lock.acquire()
        try:
            self._reset()
            lst = self._cls_instances_by_target.get(self.target, [])
            if self in lst:
                lst.remove(self)
        finally:
            self._cls_lock.release()

    @classmethod
    def watch(cls, target, on_join):
        watcher = cls(target, on_join)
        watcher.install()
        return watcher


class LogForwarder(object):
    """
    Install a :data:`mitogen.core.FORWARD_LOG` handler that delivers forwarded
    log events into the local logging framework. This is used by the master's
    :class:`Router`.

    The forwarded :class:`logging.LogRecord` objects are delivered to loggers
    under ``mitogen.ctx.*`` corresponding to their
    :attr:`mitogen.core.Context.name`, with the message prefixed with the
    logger name used in the child. The records include some extra attributes:

    * ``mitogen_message``: Unicode original message without the logger name
      prepended.
    * ``mitogen_context``: :class:`mitogen.parent.Context` reference to the
      source context.
    * ``mitogen_name``: Original logger name.

    :param mitogen.master.Router router:
        Router to install the handler on.
    """
    def __init__(self, router):
        self._router = router
        self._cache = {}
        router.add_handler(
            fn=self._on_forward_log,
            handle=mitogen.core.FORWARD_LOG,
        )

    def _on_forward_log(self, msg):
        if msg.is_dead:
            return

        logger = self._cache.get(msg.src_id)
        if logger is None:
            context = self._router.context_by_id(msg.src_id)
            if context is None:
                LOG.error('%s: dropping log from unknown context ID %d',
                          self, msg.src_id)
                return

            name = '%s.%s' % (RLOG.name, context.name)
            self._cache[msg.src_id] = logger = logging.getLogger(name)

        name, level_s, s = msg.data.decode('latin1').split('\x00', 2)
        logger.log(int(level_s), '%s: %s', name, s, extra={
            'mitogen_message': s,
            'mitogen_context': self._router.context_by_id(msg.src_id),
            'mitogen_name': name,
        })

    def __repr__(self):
        return 'LogForwarder(%r)' % (self._router,)


class ModuleFinder(object):
    """
    Given the name of a loaded module, make a best-effort attempt at finding
    related modules likely needed by a child context requesting the original
    module.
    """
    def __init__(self):
        #: Import machinery is expensive, keep :py:meth`:get_module_source`
        #: results around.
        self._found_cache = {}

        #: Avoid repeated dependency scanning, which is expensive.
        self._related_cache = {}

    def __repr__(self):
        return 'ModuleFinder()'

    def _looks_like_script(self, path):
        """
        Return :data:`True` if the (possibly extensionless) file at `path`
        resembles a Python script. For now we simply verify the file contains
        ASCII text.
        """
        fp = open(path, 'rb')
        try:
            sample = fp.read(512).decode('latin-1')
            return not set(sample).difference(string.printable)
        finally:
            fp.close()

    def _py_filename(self, path):
        if not path:
            return None

        if path[-4:] in ('.pyc', '.pyo'):
            path = path.rstrip('co')

        if path.endswith('.py'):
            return path

        if os.path.exists(path) and self._looks_like_script(path):
            return path

    def _get_module_via_pkgutil(self, fullname):
        """Attempt to fetch source code via pkgutil. In an ideal world, this
        would be the only required implementation of get_module()."""
        try:
            # Pre-'import spec' this returned None, in Python3.6 it raises
            # ImportError.
            loader = pkgutil.find_loader(fullname)
        except ImportError:
            e = sys.exc_info()[1]
            LOG.debug('%r._get_module_via_pkgutil(%r): %s',
                      self, fullname, e)
            return None

        IOLOG.debug('%r._get_module_via_pkgutil(%r) -> %r',
                    self, fullname, loader)
        if not loader:
            return

        try:
            path = self._py_filename(loader.get_filename(fullname))
            source = loader.get_source(fullname)
            is_pkg = loader.is_package(fullname)
        except (AttributeError, ImportError):
            # - Per PEP-302, get_source() and is_package() are optional,
            #   calling them may throw AttributeError.
            # - get_filename() may throw ImportError if pkgutil.find_loader()
            #   picks a "parent" package's loader for some crap that's been
            #   stuffed in sys.modules, for example in the case of urllib3:
            #       "loader for urllib3.contrib.pyopenssl cannot handle
            #        requests.packages.urllib3.contrib.pyopenssl"
            e = sys.exc_info()[1]
            LOG.debug('%r: loading %r using %r failed: %s',
                      self, fullname, loader, e)
            return

        if path is None or source is None:
            return

        if isinstance(source, mitogen.core.UnicodeType):
            # get_source() returns "string" according to PEP-302, which was
            # reinterpreted for Python 3 to mean a Unicode string.
            source = source.encode('utf-8')

        return path, source, is_pkg

    def _get_module_via_sys_modules(self, fullname):
        """Attempt to fetch source code via sys.modules. This is specifically
        to support __main__, but it may catch a few more cases."""
        module = sys.modules.get(fullname)
        LOG.debug('_get_module_via_sys_modules(%r) -> %r', fullname, module)
        if not isinstance(module, types.ModuleType):
            LOG.debug('sys.modules[%r] absent or not a regular module',
                      fullname)
            return

        path = self._py_filename(getattr(module, '__file__', ''))
        if not path:
            return

        is_pkg = hasattr(module, '__path__')
        try:
            source = inspect.getsource(module)
        except IOError:
            # Work around inspect.getsourcelines() bug for 0-byte __init__.py
            # files.
            if not is_pkg:
                raise
            source = '\n'

        if isinstance(source, mitogen.core.UnicodeType):
            # get_source() returns "string" according to PEP-302, which was
            # reinterpreted for Python 3 to mean a Unicode string.
            source = source.encode('utf-8')

        return path, source, is_pkg

    get_module_methods = [_get_module_via_pkgutil,
                          _get_module_via_sys_modules]

    def get_module_source(self, fullname):
        """Given the name of a loaded module `fullname`, attempt to find its
        source code.

        :returns:
            Tuple of `(module path, source text, is package?)`, or :data:`None`
            if the source cannot be found.
        """
        tup = self._found_cache.get(fullname)
        if tup:
            return tup

        for method in self.get_module_methods:
            tup = method(self, fullname)
            if tup:
                break
        else:
            tup = None, None, None
            LOG.debug('get_module_source(%r): cannot find source', fullname)

        self._found_cache[fullname] = tup
        return tup

    def resolve_relpath(self, fullname, level):
        """Given an ImportFrom AST node, guess the prefix that should be tacked
        on to an alias name to produce a canonical name. `fullname` is the name
        of the module in which the ImportFrom appears.
        """
        mod = sys.modules.get(fullname, None)
        if hasattr(mod, '__path__'):
            fullname += '.__init__'

        if level == 0 or not fullname:
            return ''

        bits = fullname.split('.')
        if len(bits) <= level:
            # This would be an ImportError in real code.
            return ''

        return '.'.join(bits[:-level]) + '.'

    def generate_parent_names(self, fullname):
        while '.' in fullname:
            fullname, _, _ = fullname.rpartition('.')
            yield fullname

    def find_related_imports(self, fullname):
        """
        Return a list of non-stdlib modules that are directly imported by
        `fullname`, plus their parents.

        The list is determined by retrieving the source code of
        `fullname`, compiling it, and examining all IMPORT_NAME ops.

        :param fullname: Fully qualified name of an _already imported_ module
            for which source code can be retrieved
        :type fullname: str
        """
        related = self._related_cache.get(fullname)
        if related is not None:
            return related

        modpath, src, _ = self.get_module_source(fullname)
        if src is None:
            return []

        maybe_names = list(self.generate_parent_names(fullname))

        co = compile(src, modpath, 'exec')
        for level, modname, namelist in scan_code_imports(co):
            if level == -1:
                modnames = [modname, '%s.%s' % (fullname, modname)]
            else:
                modnames = [
                    '%s%s' % (self.resolve_relpath(fullname, level), modname)
                ]

            maybe_names.extend(modnames)
            maybe_names.extend(
                '%s.%s' % (mname, name)
                for mname in modnames
                for name in namelist
            )

        return self._related_cache.setdefault(fullname, sorted(
            set(
                name
                for name in maybe_names
                if sys.modules.get(name) is not None
                and not is_stdlib_name(name)
                and u'six.moves' not in name  # TODO: crap
            )
        ))

    def find_related(self, fullname):
        """
        Return a list of non-stdlib modules that are imported directly or
        indirectly by `fullname`, plus their parents.

        This method is like :py:meth:`find_related_imports`, but also
        recursively searches any modules which are imported by `fullname`.

        :param fullname: Fully qualified name of an _already imported_ module
            for which source code can be retrieved
        :type fullname: str
        """
        stack = [fullname]
        found = set()

        while stack:
            name = stack.pop(0)
            names = self.find_related_imports(name)
            stack.extend(set(names).difference(found, stack))
            found.update(names)

        found.discard(fullname)
        return sorted(found)


class ModuleResponder(object):
    def __init__(self, router):
        self._router = router
        self._finder = ModuleFinder()
        self._cache = {}  # fullname -> pickled
        self.blacklist = []
        self.whitelist = ['']
        router.add_handler(
            fn=self._on_get_module,
            handle=mitogen.core.GET_MODULE,
        )

    def __repr__(self):
        return 'ModuleResponder(%r)' % (self._router,)

    MAIN_RE = re.compile(b(r'^if\s+__name__\s*==\s*.__main__.\s*:'), re.M)
    main_guard_msg = (
        "A child context attempted to import __main__, however the main "
        "module present in the master process lacks an execution guard. "
        "Update %r to prevent unintended execution, using a guard like:\n"
        "\n"
        "    if __name__ == '__main__':\n"
        "        # your code here.\n"
    )

    def whitelist_prefix(self, fullname):
        if self.whitelist == ['']:
            self.whitelist = ['mitogen']
        self.whitelist.append(fullname)

    def blacklist_prefix(self, fullname):
        self.blacklist.append(fullname)

    def neutralize_main(self, path, src):
        """Given the source for the __main__ module, try to find where it
        begins conditional execution based on a "if __name__ == '__main__'"
        guard, and remove any code after that point."""
        match = self.MAIN_RE.search(src)
        if match:
            return src[:match.start()]

        if b('mitogen.main(') in src:
            return src

        LOG.error(self.main_guard_msg, path)
        raise ImportError('refused')

    def _make_negative_response(self, fullname):
        return (fullname, None, None, None, ())

    def _build_tuple(self, fullname):
        if mitogen.core.is_blacklisted_import(self, fullname):
            raise ImportError('blacklisted')

        if fullname in self._cache:
            return self._cache[fullname]

        path, source, is_pkg = self._finder.get_module_source(fullname)
        if source is None:
            LOG.error('_build_tuple(%r): could not locate source', fullname)
            tup = self._make_negative_response(fullname)
            self._cache[fullname] = tup
            return tup

        if is_pkg:
            pkg_present = get_child_modules(path)
            LOG.debug('_build_tuple(%r, %r) -> %r',
                      path, fullname, pkg_present)
        else:
            pkg_present = None

        if fullname == '__main__':
            source = self.neutralize_main(path, source)
        compressed = mitogen.core.Blob(zlib.compress(source, 9))
        related = [
            to_text(name)
            for name in self._finder.find_related(fullname)
            if not mitogen.core.is_blacklisted_import(self, name)
        ]
        # 0:fullname 1:pkg_present 2:path 3:compressed 4:related
        tup = (
            to_text(fullname),
            pkg_present,
            to_text(path),
            compressed,
            related
        )
        self._cache[fullname] = tup
        return tup

    def _send_load_module(self, stream, fullname):
        if fullname not in stream.sent_modules:
            LOG.debug('_send_load_module(%r, %r)', stream, fullname)
            self._router._async_route(
                mitogen.core.Message.pickled(
                    self._build_tuple(fullname),
                    dst_id=stream.remote_id,
                    handle=mitogen.core.LOAD_MODULE,
                )
            )
            stream.sent_modules.add(fullname)

    def _send_module_load_failed(self, stream, fullname):
        stream.send(
            mitogen.core.Message.pickled(
                (fullname, None, None, None, ()),
                dst_id=stream.remote_id,
                handle=mitogen.core.LOAD_MODULE,
            )
        )

    def _send_module_and_related(self, stream, fullname):
        try:
            tup = self._build_tuple(fullname)
            if tup[2] and is_stdlib_path(tup[2]):
                # Prevent loading of 2.x<->3.x stdlib modules! This costs one
                # RTT per hit, so a client-side solution is also required.
                LOG.warning('%r: refusing to serve stdlib module %r',
                            self, fullname)
                self._send_module_load_failed(stream, fullname)
                return

            for name in tup[4]:  # related
                parent, _, _ = name.partition('.')
                if parent != fullname and parent not in stream.sent_modules:
                    # Parent hasn't been sent, so don't load submodule yet.
                    continue

                self._send_load_module(stream, name)
            self._send_load_module(stream, fullname)
        except Exception:
            LOG.debug('While importing %r', fullname, exc_info=True)
            self._send_module_load_failed(stream, fullname)

    def _on_get_module(self, msg):
        if msg.is_dead:
            return

        LOG.debug('%r._on_get_module(%r)', self, msg.data)
        stream = self._router.stream_by_id(msg.src_id)
        fullname = msg.data.decode()
        if fullname in stream.sent_modules:
            LOG.warning('_on_get_module(): dup request for %r from %r',
                        fullname, stream)

        self._send_module_and_related(stream, fullname)

    def _send_forward_module(self, stream, context, fullname):
        if stream.remote_id != context.context_id:
            stream.send(
                mitogen.core.Message(
                    data=b('%s\x00%s' % (context.context_id, fullname)),
                    handle=mitogen.core.FORWARD_MODULE,
                    dst_id=stream.remote_id,
                )
            )

    def _forward_one_module(self, context, fullname):
        path = []
        while fullname:
            path.append(fullname)
            fullname, _, _ = fullname.rpartition('.')

        for fullname in reversed(path):
            stream = self._router.stream_by_id(context.context_id)
            self._send_module_and_related(stream, fullname)
            self._send_forward_module(stream, context, fullname)

    def _forward_modules(self, context, fullnames):
        IOLOG.debug('%r._forward_modules(%r, %r)', self, context, fullnames)
        for fullname in fullnames:
            self._forward_one_module(context, fullname)

    def forward_modules(self, context, fullnames):
        self._router.broker.defer(self._forward_modules, context, fullnames)


class Broker(mitogen.core.Broker):
    shutdown_timeout = 5.0
    _watcher = None
    poller_class = mitogen.parent.PREFERRED_POLLER

    def __init__(self, install_watcher=True):
        if install_watcher:
            self._watcher = ThreadWatcher.watch(
                target=threading.currentThread(),
                on_join=self.shutdown,
            )
        super(Broker, self).__init__()

    def shutdown(self):
        super(Broker, self).shutdown()
        if self._watcher:
            self._watcher.remove()


class Router(mitogen.parent.Router):
    broker_class = Broker
    profiling = False

    def __init__(self, broker=None, max_message_size=None):
        if broker is None:
            broker = self.broker_class()
        if max_message_size:
            self.max_message_size = max_message_size
        super(Router, self).__init__(broker)
        self.upgrade()

    def upgrade(self):
        self.id_allocator = IdAllocator(self)
        self.responder = ModuleResponder(self)
        self.log_forwarder = LogForwarder(self)
        self.route_monitor = mitogen.parent.RouteMonitor(router=self)
        self.add_handler(  # TODO: cutpaste.
            fn=self._on_detaching,
            handle=mitogen.core.DETACHING,
            persist=True,
        )

    def enable_debug(self):
        mitogen.core.enable_debug_logging()
        self.debug = True

    def __enter__(self):
        return self

    def __exit__(self, e_type, e_val, tb):
        self.broker.shutdown()
        self.broker.join()

    def disconnect_stream(self, stream):
        self.broker.defer(stream.on_disconnect, self.broker)

    def disconnect_all(self):
        for stream in self._stream_by_id.values():
            self.disconnect_stream(stream)


class IdAllocator(object):
    def __init__(self, router):
        self.router = router
        self.next_id = 1
        self.lock = threading.Lock()
        router.add_handler(
            fn=self.on_allocate_id,
            handle=mitogen.core.ALLOCATE_ID,
        )

    def __repr__(self):
        return 'IdAllocator(%r)' % (self.router,)

    BLOCK_SIZE = 1000

    def allocate(self):
        self.lock.acquire()
        try:
            id_ = self.next_id
            self.next_id += 1
            return id_
        finally:
            self.lock.release()

    def allocate_block(self):
        self.lock.acquire()
        try:
            id_ = self.next_id
            self.next_id += self.BLOCK_SIZE
            end_id = id_ + self.BLOCK_SIZE
            LOG.debug('%r: allocating [%d..%d)', self, id_, end_id)
            return id_, end_id
        finally:
            self.lock.release()

    def on_allocate_id(self, msg):
        if msg.is_dead:
            return

        id_, last_id = self.allocate_block()
        requestee = self.router.context_by_id(msg.src_id)
        allocated = self.router.context_by_id(id_, msg.src_id)

        LOG.debug('%r: allocating [%r..%r) to %r',
                  self, id_, last_id, requestee)
        msg.reply((id_, last_id))
