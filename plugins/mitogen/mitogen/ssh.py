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
Functionality to allow establishing new slave contexts over an SSH connection.
"""

import logging
import re
import time

try:
    from shlex import quote as shlex_quote
except ImportError:
    from pipes import quote as shlex_quote

import mitogen.parent
from mitogen.core import b


LOG = logging.getLogger('mitogen')

# sshpass uses 'assword' because it doesn't lowercase the input.
PASSWORD_PROMPT = b('password')
HOSTKEY_REQ_PROMPT = b('are you sure you want to continue connecting (yes/no)?')
HOSTKEY_FAIL = b('host key verification failed.')

# [user@host: ] permission denied
PERMDENIED_RE = re.compile(
    ('(?:[^@]+@[^:]+: )?'  # Absent in OpenSSH <7.5
     'Permission denied').encode(),
    re.I
)


DEBUG_PREFIXES = (b('debug1:'), b('debug2:'), b('debug3:'))


def filter_debug(stream, it):
    """
    Read line chunks from it, either yielding them directly, or building up and
    logging individual lines if they look like SSH debug output.

    This contains the mess of dealing with both line-oriented input, and partial
    lines such as the password prompt.

    Yields `(line, partial)` tuples, where `line` is the line, `partial` is
    :data:`True` if no terminating newline character was present and no more
    data exists in the read buffer. Consuming code can use this to unreliably
    detect the presence of an interactive prompt.
    """
    # The `partial` test is unreliable, but is only problematic when verbosity
    # is enabled: it's possible for a combination of SSH banner, password
    # prompt, verbose output, timing and OS buffering specifics to create a
    # situation where an otherwise newline-terminated line appears to not be
    # terminated, due to a partial read(). If something is broken when
    # ssh_debug_level>0, this is the first place to look.
    state = 'start_of_line'
    buf = b('')
    for chunk in it:
        buf += chunk
        while buf:
            if state == 'start_of_line':
                if len(buf) < 8:
                    # short read near buffer limit, block awaiting at least 8
                    # bytes so we can discern a debug line, or the minimum
                    # interesting token from above or the bootstrap
                    # ('password', 'MITO000\n').
                    break
                elif buf.startswith(DEBUG_PREFIXES):
                    state = 'in_debug'
                else:
                    state = 'in_plain'
            elif state == 'in_debug':
                if b('\n') not in buf:
                    break
                line, _, buf = buf.partition(b('\n'))
                LOG.debug('%r: %s', stream, line.rstrip())
                state = 'start_of_line'
            elif state == 'in_plain':
                line, nl, buf = buf.partition(b('\n'))
                yield line + nl, not (nl or buf)
                if nl:
                    state = 'start_of_line'


class PasswordError(mitogen.core.StreamError):
    pass


class HostKeyError(mitogen.core.StreamError):
    pass


class Stream(mitogen.parent.Stream):
    child_is_immediate_subprocess = False

    #: Default to whatever is available as 'python' on the remote machine,
    #: overriding sys.executable use.
    python_path = 'python'

    #: Number of -v invocations to pass on command line.
    ssh_debug_level = 0

    #: If batch_mode=False, points to the corresponding DiagLogStream, allowing
    #: it to be disconnected at the same time this stream is being torn down.
    tty_stream = None

    #: The path to the SSH binary.
    ssh_path = 'ssh'

    hostname = None
    username = None
    port = None

    identity_file = None
    password = None
    ssh_args = None

    check_host_keys_msg = 'check_host_keys= must be set to accept, enforce or ignore'

    def construct(self, hostname, username=None, ssh_path=None, port=None,
                  check_host_keys='enforce', password=None, identity_file=None,
                  compression=True, ssh_args=None, keepalive_enabled=True,
                  keepalive_count=3, keepalive_interval=15,
                  identities_only=True, ssh_debug_level=None, **kwargs):
        super(Stream, self).construct(**kwargs)
        if check_host_keys not in ('accept', 'enforce', 'ignore'):
            raise ValueError(self.check_host_keys_msg)

        self.hostname = hostname
        self.username = username
        self.port = port
        self.check_host_keys = check_host_keys
        self.password = password
        self.identity_file = identity_file
        self.identities_only = identities_only
        self.compression = compression
        self.keepalive_enabled = keepalive_enabled
        self.keepalive_count = keepalive_count
        self.keepalive_interval = keepalive_interval
        if ssh_path:
            self.ssh_path = ssh_path
        if ssh_args:
            self.ssh_args = ssh_args
        if ssh_debug_level:
            self.ssh_debug_level = ssh_debug_level

        self._init_create_child()

    def _requires_pty(self):
        """
        Return :data:`True` if the configuration requires a PTY to be
        allocated. This is only true if we must interactively accept host keys,
        or type a password.
        """
        return (self.check_host_keys == 'accept' or
                self.password is not None)

    def _init_create_child(self):
        """
        Initialize the base class :attr:`create_child` and
        :attr:`create_child_args` according to whether we need a PTY or not.
        """
        if self._requires_pty():
            self.create_child = mitogen.parent.hybrid_tty_create_child
        else:
            self.create_child = mitogen.parent.create_child
            self.create_child_args = {
                'stderr_pipe': True,
            }

    def on_disconnect(self, broker):
        if self.tty_stream is not None:
            self.tty_stream.on_disconnect(broker)
        super(Stream, self).on_disconnect(broker)

    def get_boot_command(self):
        bits = [self.ssh_path]
        if self.ssh_debug_level:
            bits += ['-' + ('v' * min(3, self.ssh_debug_level))]
        else:
            # issue #307: suppress any login banner, as it may contain the
            # password prompt, and there is no robust way to tell the
            # difference.
            bits += ['-o', 'LogLevel ERROR']
        if self.username:
            bits += ['-l', self.username]
        if self.port is not None:
            bits += ['-p', str(self.port)]
        if self.identities_only and (self.identity_file or self.password):
            bits += ['-o', 'IdentitiesOnly yes']
        if self.identity_file:
            bits += ['-i', self.identity_file]
        if self.compression:
            bits += ['-o', 'Compression yes']
        if self.keepalive_enabled:
            bits += [
                '-o', 'ServerAliveInterval %s' % (self.keepalive_interval,),
                '-o', 'ServerAliveCountMax %s' % (self.keepalive_count,),
            ]
        if not self._requires_pty():
            bits += ['-o', 'BatchMode yes']
        if self.check_host_keys == 'enforce':
            bits += ['-o', 'StrictHostKeyChecking yes']
        if self.check_host_keys == 'accept':
            bits += ['-o', 'StrictHostKeyChecking ask']
        elif self.check_host_keys == 'ignore':
            bits += [
                '-o', 'StrictHostKeyChecking no',
                '-o', 'UserKnownHostsFile /dev/null',
                '-o', 'GlobalKnownHostsFile /dev/null',
            ]
        if self.ssh_args:
            bits += self.ssh_args
        bits.append(self.hostname)
        base = super(Stream, self).get_boot_command()
        return bits + [shlex_quote(s).strip() for s in base]

    def connect(self):
        super(Stream, self).connect()
        self.name = u'ssh.' + mitogen.core.to_text(self.hostname)
        if self.port:
            self.name += u':%s' % (self.port,)

    auth_incorrect_msg = 'SSH authentication is incorrect'
    password_incorrect_msg = 'SSH password is incorrect'
    password_required_msg = 'SSH password was requested, but none specified'
    hostkey_config_msg = (
        'SSH requested permission to accept unknown host key, but '
        'check_host_keys=ignore. This is likely due to ssh_args=  '
        'conflicting with check_host_keys=. Please correct your '
        'configuration.'
    )
    hostkey_failed_msg = (
        'Host key checking is enabled, and SSH reported an unrecognized or '
        'mismatching host key.'
    )

    def _host_key_prompt(self):
        if self.check_host_keys == 'accept':
            LOG.debug('%r: accepting host key', self)
            self.tty_stream.transmit_side.write(b('yes\n'))
            return

        # _host_key_prompt() should never be reached with ignore or enforce
        # mode, SSH should have handled that. User's ssh_args= is conflicting
        # with ours.
        raise HostKeyError(self.hostkey_config_msg)

    def _ec0_received(self):
        if self.tty_stream is not None:
            self._router.broker.start_receive(self.tty_stream)
        return super(Stream, self)._ec0_received()

    def _connect_bootstrap(self, extra_fd):
        fds = [self.receive_side.fd]
        if extra_fd is not None:
            self.tty_stream = mitogen.parent.DiagLogStream(extra_fd, self)
            fds.append(extra_fd)

        it = mitogen.parent.iter_read(fds=fds, deadline=self.connect_deadline)

        password_sent = False
        for buf, partial in filter_debug(self, it):
            LOG.debug('%r: received %r', self, buf)
            if buf.endswith(self.EC0_MARKER):
                self._ec0_received()
                return
            elif HOSTKEY_REQ_PROMPT in buf.lower():
                self._host_key_prompt()
            elif HOSTKEY_FAIL in buf.lower():
                raise HostKeyError(self.hostkey_failed_msg)
            elif PERMDENIED_RE.match(buf):
                # issue #271: work around conflict with user shell reporting
                # 'permission denied' e.g. during chdir($HOME) by only matching
                # it at the start of the line.
                if self.password is not None and password_sent:
                    raise PasswordError(self.password_incorrect_msg)
                elif PASSWORD_PROMPT in buf and self.password is None:
                    # Permission denied (password,pubkey)
                    raise PasswordError(self.password_required_msg)
                else:
                    raise PasswordError(self.auth_incorrect_msg)
            elif partial and PASSWORD_PROMPT in buf.lower():
                if self.password is None:
                    raise PasswordError(self.password_required_msg)
                LOG.debug('%r: sending password', self)
                self.tty_stream.transmit_side.write(
                    (self.password + '\n').encode()
                )
                password_sent = True

        raise mitogen.core.StreamError('bootstrap failed')
