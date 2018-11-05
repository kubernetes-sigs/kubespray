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

from __future__ import absolute_import
import atexit
import errno
import logging
import os
import signal
import socket
import sys
import time

try:
    import faulthandler
except ImportError:
    faulthandler = None

import mitogen
import mitogen.core
import mitogen.debug
import mitogen.master
import mitogen.parent
import mitogen.service
import mitogen.unix
import mitogen.utils

import ansible.constants as C
import ansible_mitogen.logging
import ansible_mitogen.services

from mitogen.core import b


LOG = logging.getLogger(__name__)


def clean_shutdown(sock):
    """
    Shut the write end of `sock`, causing `recv` in the worker process to wake
    up with a 0-byte read and initiate mux process exit, then wait for a 0-byte
    read from the read end, which will occur after the the child closes the
    descriptor on exit.

    This is done using :mod:`atexit` since Ansible lacks any more sensible hook
    to run code during exit, and unless some synchronization exists with
    MuxProcess, debug logs may appear on the user's terminal *after* the prompt
    has been printed.
    """
    sock.shutdown(socket.SHUT_WR)
    sock.recv(1)


def getenv_int(key, default=0):
    """
    Get an integer-valued environment variable `key`, if it exists and parses
    as an integer, otherwise return `default`.
    """
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


def setup_gil():
    """
    Set extremely long GIL release interval to let threads naturally progress
    through CPU-heavy sequences without forcing the wake of another thread that
    may contend trying to run the same CPU-heavy code. For the new-style work,
    this drops runtime ~33% and involuntary context switches by >80%,
    essentially making threads cooperatively scheduled.
    """
    try:
        # Python 2.
        sys.setcheckinterval(100000)
    except AttributeError:
        pass

    try:
        # Python 3.
        sys.setswitchinterval(10)
    except AttributeError:
        pass


class MuxProcess(object):
    """
    Implement a subprocess forked from the Ansible top-level, as a safe place
    to contain the Mitogen IO multiplexer thread, keeping its use of the
    logging package (and the logging package's heavy use of locks) far away
    from the clutches of os.fork(), which is used continuously by the
    multiprocessing package in the top-level process.

    The problem with running the multiplexer in that process is that should the
    multiplexer thread be in the process of emitting a log entry (and holding
    its lock) at the point of fork, in the child, the first attempt to log any
    log entry using the same handler will deadlock the child, as in the memory
    image the child received, the lock will always be marked held.

    See https://bugs.python.org/issue6721 for a thorough description of the
    class of problems this worker is intended to avoid.
    """

    #: In the top-level process, this references one end of a socketpair(),
    #: which the MuxProcess blocks reading from in order to determine when
    #: the master process dies. Once the read returns, the MuxProcess will
    #: begin shutting itself down.
    worker_sock = None

    #: In the worker process, this references the other end of
    #: :py:attr:`worker_sock`.
    child_sock = None

    #: In the top-level process, this is the PID of the single MuxProcess
    #: that was spawned.
    worker_pid = None

    #: A copy of :data:`os.environ` at the time the multiplexer process was
    #: started. It's used by mitogen_local.py to find changes made to the
    #: top-level environment (e.g. vars plugins -- issue #297) that must be
    #: applied to locally executed commands and modules.
    original_env = None

    #: In both processes, this is the temporary UNIX socket used for
    #: forked WorkerProcesses to contact the MuxProcess
    unix_listener_path = None

    #: Singleton.
    _instance = None

    @classmethod
    def start(cls):
        """
        Arrange for the subprocess to be started, if it is not already running.

        The parent process picks a UNIX socket path the child will use prior to
        fork, creates a socketpair used essentially as a semaphore, then blocks
        waiting for the child to indicate the UNIX socket is ready for use.
        """
        if cls.worker_sock is not None:
            return

        if faulthandler is not None:
            faulthandler.enable()

        setup_gil()
        cls.unix_listener_path = mitogen.unix.make_socket_path()
        cls.worker_sock, cls.child_sock = socket.socketpair()
        atexit.register(lambda: clean_shutdown(cls.worker_sock))
        mitogen.core.set_cloexec(cls.worker_sock.fileno())
        mitogen.core.set_cloexec(cls.child_sock.fileno())

        if os.environ.get('MITOGEN_PROFILING'):
            mitogen.core.enable_profiling()

        cls.original_env = dict(os.environ)
        cls.child_pid = os.fork()
        ansible_mitogen.logging.setup()
        if cls.child_pid:
            cls.child_sock.close()
            cls.child_sock = None
            mitogen.core.io_op(cls.worker_sock.recv, 1)
        else:
            cls.worker_sock.close()
            cls.worker_sock = None
            self = cls()
            self.worker_main()
            sys.exit()

    def worker_main(self):
        """
        The main function of for the mux process: setup the Mitogen broker
        thread and ansible_mitogen services, then sleep waiting for the socket
        connected to the parent to be closed (indicating the parent has died).
        """
        self._setup_master()
        self._setup_services()

        # Let the parent know our listening socket is ready.
        mitogen.core.io_op(self.child_sock.send, b('1'))
        # Block until the socket is closed, which happens on parent exit.
        mitogen.core.io_op(self.child_sock.recv, 1)

    def _enable_router_debug(self):
        if 'MITOGEN_ROUTER_DEBUG' in os.environ:
            self.router.enable_debug()

    def _enable_stack_dumps(self):
        secs = getenv_int('MITOGEN_DUMP_THREAD_STACKS', default=0)
        if secs:
            mitogen.debug.dump_to_logger(secs=secs)

    def _setup_master(self):
        """
        Construct a Router, Broker, and mitogen.unix listener
        """
        self.router = mitogen.master.Router(max_message_size=4096 * 1048576)
        self.router.responder.whitelist_prefix('ansible')
        self.router.responder.whitelist_prefix('ansible_mitogen')
        mitogen.core.listen(self.router.broker, 'shutdown', self.on_broker_shutdown)
        mitogen.core.listen(self.router.broker, 'exit', self.on_broker_exit)
        self.listener = mitogen.unix.Listener(
            router=self.router,
            path=self.unix_listener_path,
            backlog=C.DEFAULT_FORKS,
        )
        self._enable_router_debug()
        self._enable_stack_dumps()

    def _setup_services(self):
        """
        Construct a ContextService and a thread to service requests for it
        arriving from worker processes.
        """
        self.pool = mitogen.service.Pool(
            router=self.router,
            services=[
                mitogen.service.FileService(router=self.router),
                mitogen.service.PushFileService(router=self.router),
                ansible_mitogen.services.ContextService(self.router),
                ansible_mitogen.services.ModuleDepService(self.router),
            ],
            size=getenv_int('MITOGEN_POOL_SIZE', default=16),
        )
        LOG.debug('Service pool configured: size=%d', self.pool.size)

    def on_broker_shutdown(self):
        """
        Respond to broker shutdown by beginning service pool shutdown. Do not
        join on the pool yet, since that would block the broker thread which
        then cannot clean up pending handlers, which is required for the
        threads to exit gracefully.
        """
        self.pool.stop(join=False)
        try:
            os.unlink(self.listener.path)
        except OSError as e:
            # Prevent a shutdown race with the parent process.
            if e.args[0] != errno.ENOENT:
                raise

    def on_broker_exit(self):
        """
        Respond to the broker thread about to exit by sending SIGTERM to
        ourself. In future this should gracefully join the pool, but TERM is
        fine for now.
        """
        if os.environ.get('MITOGEN_PROFILING'):
            # TODO: avoid killing pool threads before they have written their
            # .pstats. Really shouldn't be using kill() here at all, but hard
            # to guarantee services can always be unblocked during shutdown.
            time.sleep(1)

        os.kill(os.getpid(), signal.SIGTERM)
