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

import logging
import os
import random
import sys
import threading
import traceback

import mitogen.core
import mitogen.parent


LOG = logging.getLogger('mitogen')


def fixup_prngs():
    """
    Add 256 bits of /dev/urandom to OpenSSL's PRNG in the child, and re-seed
    the random package with the same data.
    """
    s = os.urandom(256 // 8)
    random.seed(s)
    if 'ssl' in sys.modules:
        sys.modules['ssl'].RAND_add(s, 75.0)


def reset_logging_framework():
    """
    After fork, ensure any logging.Handler locks are recreated, as a variety of
    threads in the parent may have been using the logging package at the moment
    of fork.

    It is not possible to solve this problem in general; see
    https://github.com/dw/mitogen/issues/150 for a full discussion.
    """
    logging._lock = threading.RLock()

    # The root logger does not appear in the loggerDict.
    for name in [None] + list(logging.Logger.manager.loggerDict):
        for handler in logging.getLogger(name).handlers:
            handler.createLock()

    root = logging.getLogger()
    root.handlers = [
        handler
        for handler in root.handlers
        if not isinstance(handler, mitogen.core.LogHandler)
    ]


def on_fork():
    """
    Should be called by any program integrating Mitogen each time the process
    is forked, in the context of the new child.
    """
    reset_logging_framework()  # Must be first!
    fixup_prngs()
    mitogen.core.Latch._on_fork()
    mitogen.core.Side._on_fork()


def handle_child_crash():
    """
    Respond to _child_main() crashing by ensuring the relevant exception is
    logged to /dev/tty.
    """
    tty = open('/dev/tty', 'wb')
    tty.write('\n\nFORKED CHILD PID %d CRASHED\n%s\n\n' % (
        os.getpid(),
        traceback.format_exc(),
    ))
    tty.close()
    os._exit(1)


class Stream(mitogen.parent.Stream):
    child_is_immediate_subprocess = True

    #: Reference to the importer, if any, recovered from the parent.
    importer = None

    #: User-supplied function for cleaning up child process state.
    on_fork = None

    def construct(self, old_router, max_message_size, on_fork=None,
                  debug=False, profiling=False, unidirectional=False,
                  on_start=None):
        # fork method only supports a tiny subset of options.
        super(Stream, self).construct(max_message_size=max_message_size,
                                      debug=debug, profiling=profiling,
                                      unidirectional=False)
        self.on_fork = on_fork
        self.on_start = on_start

        responder = getattr(old_router, 'responder', None)
        if isinstance(responder, mitogen.parent.ModuleForwarder):
            self.importer = responder.importer

    name_prefix = u'fork'

    def start_child(self):
        parentfp, childfp = mitogen.parent.create_socketpair()
        self.pid = os.fork()
        if self.pid:
            childfp.close()
            # Decouple the socket from the lifetime of the Python socket object.
            fd = os.dup(parentfp.fileno())
            parentfp.close()
            return self.pid, fd, None
        else:
            parentfp.close()
            self._wrap_child_main(childfp)

    def _wrap_child_main(self, childfp):
        try:
            self._child_main(childfp)
        except BaseException:
            handle_child_crash()

    def _child_main(self, childfp):
        on_fork()
        if self.on_fork:
            self.on_fork()
        mitogen.core.set_block(childfp.fileno())

        # Expected by the ExternalContext.main().
        os.dup2(childfp.fileno(), 1)
        os.dup2(childfp.fileno(), 100)

        # Overwritten by ExternalContext.main(); we must replace the
        # parent-inherited descriptors that were closed by Side._on_fork() to
        # avoid ExternalContext.main() accidentally allocating new files over
        # the standard handles.
        os.dup2(childfp.fileno(), 0)

        # Avoid corrupting the stream on fork crash by dupping /dev/null over
        # stderr. Instead, handle_child_crash() uses /dev/tty to log errors.
        devnull = os.open('/dev/null', os.O_WRONLY)
        if devnull != 2:
            os.dup2(devnull, 2)
            os.close(devnull)

        # If we're unlucky, childfp.fileno() may coincidentally be one of our
        # desired FDs. In that case closing it breaks ExternalContext.main().
        if childfp.fileno() not in (0, 1, 100):
            childfp.close()

        config = self.get_econtext_config()
        config['core_src_fd'] = None
        config['importer'] = self.importer
        config['setup_package'] = False
        if self.on_start:
            config['on_start'] = self.on_start

        try:
            mitogen.core.ExternalContext(config).main()
        except Exception:
            # TODO: report exception somehow.
            os._exit(72)
        finally:
            # Don't trigger atexit handlers, they were copied from the parent.
            os._exit(0)

    def _connect_bootstrap(self, extra_fd):
        # None required.
        pass
