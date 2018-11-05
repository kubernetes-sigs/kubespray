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
Permit connection of additional contexts that may act with the authority of
this context. For now, the UNIX socket is always mode 0600, i.e. can only be
accessed by root or the same UID. Therefore we can always trust connections to
have the same privilege (auth_id) as the current process.
"""

import errno
import os
import socket
import struct
import sys
import tempfile

import mitogen.core
import mitogen.master

from mitogen.core import LOG


def is_path_dead(path):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(path)
    except socket.error:
        e = sys.exc_info()[1]
        return e.args[0] in (errno.ECONNREFUSED, errno.ENOENT)
    return False


def make_socket_path():
    return tempfile.mktemp(prefix='mitogen_unix_')


class Listener(mitogen.core.BasicStream):
    keep_alive = True

    def __init__(self, router, path=None, backlog=100):
        self._router = router
        self.path = path or make_socket_path()
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        if os.path.exists(self.path) and is_path_dead(self.path):
            LOG.debug('%r: deleting stale %r', self, self.path)
            os.unlink(self.path)

        self._sock.bind(self.path)
        os.chmod(self.path, int('0600', 8))
        self._sock.listen(backlog)
        self.receive_side = mitogen.core.Side(self, self._sock.fileno())
        router.broker.start_receive(self)

    def _accept_client(self, sock):
        sock.setblocking(True)
        try:
            pid, = struct.unpack('>L', sock.recv(4))
        except (struct.error, socket.error):
            LOG.error('%r: failed to read remote identity: %s',
                      self, sys.exc_info()[1])
            return

        context_id = self._router.id_allocator.allocate()
        context = mitogen.parent.Context(self._router, context_id)
        stream = mitogen.core.Stream(self._router, context_id)
        stream.name = u'unix_client.%d' % (pid,)
        stream.auth_id = mitogen.context_id
        stream.is_privileged = True

        try:
            sock.send(struct.pack('>LLL', context_id, mitogen.context_id,
                                  os.getpid()))
        except socket.error:
            LOG.error('%r: failed to assign identity to PID %d: %s',
                      self, pid, sys.exc_info()[1])
            return

        stream.accept(sock.fileno(), sock.fileno())
        self._router.register(context, stream)

    def on_receive(self, broker):
        sock, _ = self._sock.accept()
        try:
            self._accept_client(sock)
        finally:
            sock.close()


def connect(path, broker=None):
    LOG.debug('unix.connect(path=%r)', path)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    sock.send(struct.pack('>L', os.getpid()))
    mitogen.context_id, remote_id, pid = struct.unpack('>LLL', sock.recv(12))
    mitogen.parent_id = remote_id
    mitogen.parent_ids = [remote_id]

    LOG.debug('unix.connect(): local ID is %r, remote is %r',
              mitogen.context_id, remote_id)

    router = mitogen.master.Router(broker=broker)
    stream = mitogen.core.Stream(router, remote_id)
    stream.accept(sock.fileno(), sock.fileno())
    stream.name = u'unix_listener.%d' % (pid,)

    context = mitogen.parent.Context(router, remote_id)
    router.register(context, stream)

    mitogen.core.listen(router.broker, 'shutdown',
                        lambda: router.disconnect_stream(stream))

    sock.close()
    return router, context
