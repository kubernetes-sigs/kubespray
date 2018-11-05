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
Basic signal handler for dumping thread stacks.
"""

import difflib
import logging
import os
import gc
import signal
import sys
import threading
import time
import traceback

import mitogen.core
import mitogen.parent


LOG = logging.getLogger(__name__)
_last = None


def enable_evil_interrupts():
    signal.signal(signal.SIGALRM, (lambda a, b: None))
    signal.setitimer(signal.ITIMER_REAL, 0.01, 0.01)


def disable_evil_interrupts():
    signal.setitimer(signal.ITIMER_REAL, 0, 0)


def _hex(n):
    return '%08x' % n


def get_subclasses(klass):
    """
    Rather than statically import every interesting subclass, forcing it all to
    be transferred and potentially disrupting the debugged environment,
    enumerate only those loaded in memory. Also returns the original class.
    """
    stack = [klass]
    seen = set()
    while stack:
        klass = stack.pop()
        seen.add(klass)
        stack.extend(klass.__subclasses__())
    return seen


def get_routers():
    return dict(
        (_hex(id(router)), router)
        for klass in get_subclasses(mitogen.core.Router)
        for router in gc.get_referrers(klass)
        if isinstance(router, mitogen.core.Router)
    )


def get_router_info():
    return {
        'routers': dict(
            (id_, {
                'id': id_,
                'streams': len(set(router._stream_by_id.values())),
                'contexts': len(set(router._context_by_id.values())),
                'handles': len(router._handle_map),
            })
            for id_, router in get_routers().items()
        )
    }


def get_router_info(router):
    pass


def get_stream_info(router_id):
    router = get_routers().get(router_id)
    return {
        'streams': dict(
            (_hex(id(stream)), ({
                'name': stream.name,
                'remote_id': stream.remote_id,
                'sent_module_count': len(getattr(stream, 'sent_modules', [])),
                'routes': sorted(getattr(stream, 'routes', [])),
                'type': type(stream).__module__,
            }))
            for via_id, stream in router._stream_by_id.items()
        )
    }


def format_stacks():
    name_by_id = dict(
        (t.ident, t.name)
        for t in threading.enumerate()
    )

    l = ['', '']
    for threadId, stack in sys._current_frames().items():
        l += ["# PID %d ThreadID: (%s) %s; %r" % (
            os.getpid(),
            name_by_id.get(threadId, '<no name>'),
            threadId,
            stack,
        )]
        #stack = stack.f_back.f_back

        for filename, lineno, name, line in traceback.extract_stack(stack):
            l += [
                'File: "%s", line %d, in %s' % (
                    filename,
                    lineno,
                    name
                )
            ]
            if line:
                l += ['    ' + line.strip()]
        l += ['']

    l += ['', '']
    return '\n'.join(l)


def get_snapshot():
    global _last

    s = format_stacks()
    snap = s
    if _last:
        snap += '\n'
        diff = list(difflib.unified_diff(
            a=_last.splitlines(),
            b=s.splitlines(),
            fromfile='then',
            tofile='now'
        ))

        if diff:
            snap += '\n'.join(diff) + '\n'
        else:
            snap += '(no change since last time)\n'
    _last = s
    return snap


def _handler(*_):
    fp = open('/dev/tty', 'w', 1)
    fp.write(get_snapshot())
    fp.close()


def install_handler():
    signal.signal(signal.SIGUSR2, _handler)


def _logging_main(secs):
    while True:
        time.sleep(secs)
        LOG.info('PERIODIC THREAD DUMP\n\n%s', get_snapshot())


def dump_to_logger(secs=5):
    th = threading.Thread(
        target=_logging_main,
        kwargs={'secs': secs},
        name='mitogen.debug.dump_to_logger',
    )
    th.setDaemon(True)
    th.start()


class ContextDebugger(object):
    @classmethod
    @mitogen.core.takes_econtext
    def _configure_context(cls, econtext):
        mitogen.parent.upgrade_router(econtext)
        econtext.debugger = cls(econtext.router)

    def __init__(self, router):
        self.router = router
        self.router.add_handler(
            func=self._on_debug_msg,
            handle=mitogen.core.DEBUG,
            persist=True,
            policy=mitogen.core.has_parent_authority,
        )
        mitogen.core.listen(router, 'register', self._on_stream_register)
        LOG.debug('Context debugging configured.')

    def _on_stream_register(self, context, stream):
        LOG.debug('_on_stream_register: sending configure() to %r', stream)
        context.call_async(ContextDebugger._configure_context)

    def _on_debug_msg(self, msg):
        if msg != mitogen.core._DEAD:
            threading.Thread(
                target=self._handle_debug_msg,
                name='ContextDebuggerHandler',
                args=(msg,)
            ).start()

    def _handle_debug_msg(self, msg):
        try:
            method, args, kwargs = msg.unpickle()
            msg.reply(getattr(cls, method)(*args, **kwargs))
        except Exception:
            e = sys.exc_info()[1]
            msg.reply(mitogen.core.CallError(e))
