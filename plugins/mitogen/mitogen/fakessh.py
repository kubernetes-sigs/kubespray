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
:mod:`mitogen.fakessh` is a stream implementation that starts a subprocess with
its environment modified such that ``PATH`` searches for `ssh` return a Mitogen
implementation of SSH. When invoked, this implementation arranges for the
command line supplied by the caller to be executed in a remote context, reusing
the parent context's (possibly proxied) connection to that remote context.

This allows tools like `rsync` and `scp` to transparently reuse the connections
and tunnels already established by the host program to connect to a target
machine, without wasteful redundant SSH connection setup, 3-way handshakes, or
firewall hopping configurations, and enables these tools to be used in
impossible scenarios, such as over `sudo` with ``requiretty`` enabled.

The fake `ssh` command source is written to a temporary file on disk, and
consists of a copy of the :py:mod:`mitogen.core` source code (just like any
other child context), with a line appended to cause it to connect back to the
host process over an FD it inherits. As there is no reliance on an existing
filesystem file, it is possible for child contexts to use fakessh.

As a consequence of connecting back through an inherited FD, only one SSH
invocation is possible, which is fine for tools like `rsync`, however in future
this restriction will be lifted.

Sequence:

    1. ``fakessh`` Context and Stream created by parent context. The stream's
       buffer has a :py:func:`_fakessh_main` :py:data:`CALL_FUNCTION
       <mitogen.core.CALL_FUNCTION>` enqueued.
    2. Target program (`rsync/scp/sftp`) invoked, which internally executes
       `ssh` from ``PATH``.
    3. :py:mod:`mitogen.core` bootstrap begins, recovers the stream FD
       inherited via the target program, established itself as the fakessh
       context.
    4. :py:func:`_fakessh_main` :py:data:`CALL_FUNCTION
       <mitogen.core.CALL_FUNCTION>` is read by fakessh context,

        a. sets up :py:class:`IoPump` for stdio, registers
           stdin_handle for local context.
        b. Enqueues :py:data:`CALL_FUNCTION <mitogen.core.CALL_FUNCTION>` for
           :py:func:`_start_slave` invoked in target context,

            i. the program from the `ssh` command line is started
            ii. sets up :py:class:`IoPump` for `ssh` command line process's
                stdio pipes
            iii. returns `(control_handle, stdin_handle)` to
                 :py:func:`_fakessh_main`

    5. :py:func:`_fakessh_main` receives control/stdin handles from from
       :py:func:`_start_slave`,

        a. registers remote's stdin_handle with local :py:class:`IoPump`.
        b. sends `("start", local_stdin_handle)` to remote's control_handle
        c. registers local :py:class:`IoPump` with
           :py:class:`mitogen.core.Broker`.
        d. loops waiting for `local stdout closed && remote stdout closed`

    6. :py:func:`_start_slave` control channel receives `("start", stdin_handle)`,

        a. registers remote's stdin_handle with local :py:class:`IoPump`
        b. registers local :py:class:`IoPump` with
           :py:class:`mitogen.core.Broker`.
        c. loops waiting for `local stdout closed && remote stdout closed`
"""

import getopt
import inspect
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

import mitogen.core
import mitogen.master
import mitogen.parent

from mitogen.core import LOG, IOLOG


SSH_GETOPTS = (
    "1246ab:c:e:fgi:kl:m:no:p:qstvx"
    "ACD:E:F:I:KL:MNO:PQ:R:S:TVw:W:XYy"
)

_mitogen = None


class IoPump(mitogen.core.BasicStream):
    _output_buf = ''
    _closed = False

    def __init__(self, broker, stdin_fd, stdout_fd):
        self._broker = broker
        self.receive_side = mitogen.core.Side(self, stdout_fd)
        self.transmit_side = mitogen.core.Side(self, stdin_fd)

    def write(self, s):
        self._output_buf += s
        self._broker._start_transmit(self)

    def close(self):
        self._closed = True
        # If local process hasn't exitted yet, ensure its write buffer is
        # drained before lazily triggering disconnect in on_transmit.
        if self.transmit_side.fd is not None:
            self._broker._start_transmit(self)

    def on_shutdown(self, broker):
        self.close()

    def on_transmit(self, broker):
        written = self.transmit_side.write(self._output_buf)
        IOLOG.debug('%r.on_transmit() -> len %r', self, written)
        if written is None:
            self.on_disconnect(broker)
        else:
            self._output_buf = self._output_buf[written:]

        if not self._output_buf:
            broker._stop_transmit(self)
            if self._closed:
                self.on_disconnect(broker)

    def on_receive(self, broker):
        s = self.receive_side.read()
        IOLOG.debug('%r.on_receive() -> len %r', self, len(s))
        if s:
            mitogen.core.fire(self, 'receive', s)
        else:
            self.on_disconnect(broker)

    def __repr__(self):
        return 'IoPump(%r, %r)' % (
            self.receive_side.fd,
            self.transmit_side.fd,
        )


class Process(object):
    """
    Manages the lifetime and pipe connections of the SSH command running in the
    slave.
    """
    def __init__(self, router, stdin_fd, stdout_fd, proc=None):
        self.router = router
        self.stdin_fd = stdin_fd
        self.stdout_fd = stdout_fd
        self.proc = proc
        self.control_handle = router.add_handler(self._on_control)
        self.stdin_handle = router.add_handler(self._on_stdin)
        self.pump = IoPump(router.broker, stdin_fd, stdout_fd)
        self.stdin = None
        self.control = None
        self.wake_event = threading.Event()

        mitogen.core.listen(self.pump, 'disconnect', self._on_pump_disconnect)
        mitogen.core.listen(self.pump, 'receive', self._on_pump_receive)

        if proc:
            pmon = mitogen.parent.ProcessMonitor.instance()
            pmon.add(proc.pid, self._on_proc_exit)

    def __repr__(self):
        return 'Process(%r, %r)' % (self.stdin_fd, self.stdout_fd)

    def _on_proc_exit(self, status):
        LOG.debug('%r._on_proc_exit(%r)', self, status)
        self.control.put(('exit', status))

    def _on_stdin(self, msg):
        if msg.is_dead:
            IOLOG.debug('%r._on_stdin() -> %r', self, data)
            self.pump.close()
            return

        data = msg.unpickle()
        IOLOG.debug('%r._on_stdin() -> len %d', self, len(data))
        self.pump.write(data)

    def _on_control(self, msg):
        if not msg.is_dead:
            command, arg = msg.unpickle(throw=False)
            LOG.debug('%r._on_control(%r, %s)', self, command, arg)

            func = getattr(self, '_on_%s' % (command,), None)
            if func:
                return func(msg, arg)

            LOG.warning('%r: unknown command %r', self, command)

    def _on_start(self, msg, arg):
        dest = mitogen.core.Context(self.router, msg.src_id)
        self.control = mitogen.core.Sender(dest, arg[0])
        self.stdin = mitogen.core.Sender(dest, arg[1])
        self.router.broker.start_receive(self.pump)

    def _on_exit(self, msg, arg):
        LOG.debug('on_exit: proc = %r', self.proc)
        if self.proc:
            self.proc.terminate()
        else:
            self.router.broker.shutdown()

    def _on_pump_receive(self, s):
        IOLOG.info('%r._on_pump_receive(len %d)', self, len(s))
        self.stdin.put(s)

    def _on_pump_disconnect(self):
        LOG.debug('%r._on_pump_disconnect()', self)
        mitogen.core.fire(self, 'disconnect')
        self.stdin.close()
        self.wake_event.set()

    def start_master(self, stdin, control):
        self.stdin = stdin
        self.control = control
        control.put(('start', (self.control_handle, self.stdin_handle)))
        self.router.broker.start_receive(self.pump)

    def wait(self):
        while not self.wake_event.isSet():
            # Timeout is used so that sleep is interruptible, as blocking
            # variants of libc thread operations cannot be interrupted e.g. via
            # KeyboardInterrupt. isSet() test and wait() are separate since in
            # <2.7 wait() always returns None.
            self.wake_event.wait(0.1)


@mitogen.core.takes_router
def _start_slave(src_id, cmdline, router):
    """
    This runs in the target context, it is invoked by _fakessh_main running in
    the fakessh context immediately after startup. It starts the slave process
    (the the point where it has a stdin_handle to target but not stdout_chan to
    write to), and waits for main to.
    """
    LOG.debug('_start_slave(%r, %r)', router, cmdline)

    proc = subprocess.Popen(
        cmdline,
        # SSH server always uses user's shell.
        shell=True,
        # SSH server always executes new commands in the user's HOME.
        cwd=os.path.expanduser('~'),

        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    process = Process(
        router,
        proc.stdin.fileno(),
        proc.stdout.fileno(),
        proc,
    )

    return process.control_handle, process.stdin_handle


#
# SSH client interface.
#


def exit():
    _mitogen.broker.shutdown()


def die(msg, *args):
    if args:
        msg %= args
    sys.stderr.write('%s\n' % (msg,))
    exit()


def parse_args():
    hostname = None
    remain = sys.argv[1:]
    allopts = []
    restarted = 0

    while remain and restarted < 2:
        opts, args = getopt.getopt(remain, SSH_GETOPTS)
        remain = remain[:]  # getopt bug!
        allopts += opts
        if not args:
            break

        if not hostname:
            hostname = args.pop(0)
            remain = remain[remain.index(hostname) + 1:]

        restarted += 1

    return hostname, allopts, args


@mitogen.core.takes_econtext
def _fakessh_main(dest_context_id, econtext):
    hostname, opts, args = parse_args()
    if not hostname:
        die('Missing hostname')

    subsystem = False
    for opt, optarg in opts:
        if opt == '-s':
            subsystem = True
        else:
            LOG.debug('Warning option %s %s is ignored.', opt, optarg)

    LOG.debug('hostname: %r', hostname)
    LOG.debug('opts: %r', opts)
    LOG.debug('args: %r', args)

    if subsystem:
        die('-s <subsystem> is not yet supported')

    if not args:
        die('fakessh: login mode not supported and no command specified')

    dest = mitogen.parent.Context(econtext.router, dest_context_id)

    # Even though SSH receives an argument vector, it still cats the vector
    # together before sending to the server, the server just uses /bin/sh -c to
    # run the command. We must remain puke-for-puke compatible.
    control_handle, stdin_handle = dest.call(_start_slave,
        mitogen.context_id, ' '.join(args))

    LOG.debug('_fakessh_main: received control_handle=%r, stdin_handle=%r',
              control_handle, stdin_handle)

    process = Process(econtext.router, 1, 0)
    process.start_master(
        stdin=mitogen.core.Sender(dest, stdin_handle),
        control=mitogen.core.Sender(dest, control_handle),
    )
    process.wait()
    process.control.put(('exit', None))


def _get_econtext_config(context, sock2):
    parent_ids = mitogen.parent_ids[:]
    parent_ids.insert(0, mitogen.context_id)
    return {
        'context_id': context.context_id,
        'core_src_fd': None,
        'debug': getattr(context.router, 'debug', False),
        'in_fd': sock2.fileno(),
        'log_level': mitogen.parent.get_log_level(),
        'max_message_size': context.router.max_message_size,
        'out_fd': sock2.fileno(),
        'parent_ids': parent_ids,
        'profiling': getattr(context.router, 'profiling', False),
        'unidirectional': getattr(context.router, 'unidirectional', False),
        'setup_stdio': False,
        'version': mitogen.__version__,
    }


#
# Public API.
#

@mitogen.core.takes_econtext
@mitogen.core.takes_router
def run(dest, router, args, deadline=None, econtext=None):
    """
    Run the command specified by `args` such that ``PATH`` searches for SSH by
    the command will cause its attempt to use SSH to execute a remote program
    to be redirected to use mitogen to execute that program using the context
    `dest` instead.

    :param list args:
        Argument vector.
    :param mitogen.core.Context dest:
        The destination context to execute the SSH command line in.

    :param mitogen.core.Router router:

    :param list[str] args:
        Command line arguments for local program, e.g.
        ``['rsync', '/tmp', 'remote:/tmp']``

    :returns:
        Exit status of the child process.
    """
    if econtext is not None:
        mitogen.parent.upgrade_router(econtext)

    context_id = router.allocate_id()
    fakessh = mitogen.parent.Context(router, context_id)
    fakessh.name = u'fakessh.%d' % (context_id,)

    sock1, sock2 = socket.socketpair()

    stream = mitogen.core.Stream(router, context_id)
    stream.name = u'fakessh'
    stream.accept(sock1.fileno(), sock1.fileno())
    router.register(fakessh, stream)

    # Held in socket buffer until process is booted.
    fakessh.call_async(_fakessh_main, dest.context_id)

    tmp_path = tempfile.mkdtemp(prefix='mitogen_fakessh')
    try:
        ssh_path = os.path.join(tmp_path, 'ssh')
        fp = open(ssh_path, 'w')
        try:
            fp.write('#!%s\n' % (mitogen.parent.get_sys_executable(),))
            fp.write(inspect.getsource(mitogen.core))
            fp.write('\n')
            fp.write('ExternalContext(%r).main()\n' % (
                _get_econtext_config(context, sock2),
            ))
        finally:
            fp.close()

        os.chmod(ssh_path, int('0755', 8))
        env = os.environ.copy()
        env.update({
            'PATH': '%s:%s' % (tmp_path, env.get('PATH', '')),
            'ARGV0': mitogen.parent.get_sys_executable(),
            'SSH_PATH': ssh_path,
        })

        proc = subprocess.Popen(args, env=env)
        return proc.wait()
    finally:
        shutil.rmtree(tmp_path)
