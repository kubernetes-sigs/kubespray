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

import mitogen.core
import mitogen.parent
from mitogen.core import b


LOG = logging.getLogger(__name__)


class PasswordError(mitogen.core.StreamError):
    pass


class Stream(mitogen.parent.Stream):
    create_child = staticmethod(mitogen.parent.hybrid_tty_create_child)
    child_is_immediate_subprocess = False

    #: Once connected, points to the corresponding DiagLogStream, allowing it
    #: to be disconnected at the same time this stream is being torn down.
    tty_stream = None

    username = 'root'
    password = None
    doas_path = 'doas'
    password_prompt = b('Password:')
    incorrect_prompts = (
        b('doas: authentication failed'),
    )

    def construct(self, username=None, password=None, doas_path=None,
                  password_prompt=None, incorrect_prompts=None, **kwargs):
        super(Stream, self).construct(**kwargs)
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if doas_path is not None:
            self.doas_path = doas_path
        if password_prompt is not None:
            self.password_prompt = password_prompt.lower()
        if incorrect_prompts is not None:
            self.incorrect_prompts = map(str.lower, incorrect_prompts)

    def connect(self):
        super(Stream, self).connect()
        self.name = u'doas.' + mitogen.core.to_text(self.username)

    def on_disconnect(self, broker):
        self.tty_stream.on_disconnect(broker)
        super(Stream, self).on_disconnect(broker)

    def get_boot_command(self):
        bits = [self.doas_path, '-u', self.username, '--']
        bits = bits + super(Stream, self).get_boot_command()
        LOG.debug('doas command line: %r', bits)
        return bits

    password_incorrect_msg = 'doas password is incorrect'
    password_required_msg = 'doas password is required'

    def _connect_bootstrap(self, extra_fd):
        self.tty_stream = mitogen.parent.DiagLogStream(extra_fd, self)

        password_sent = False
        it = mitogen.parent.iter_read(
            fds=[self.receive_side.fd, extra_fd],
            deadline=self.connect_deadline,
        )

        for buf in it:
            LOG.debug('%r: received %r', self, buf)
            if buf.endswith(self.EC0_MARKER):
                self._ec0_received()
                return
            if any(s in buf.lower() for s in self.incorrect_prompts):
                if password_sent:
                    raise PasswordError(self.password_incorrect_msg)
            elif self.password_prompt in buf.lower():
                if self.password is None:
                    raise PasswordError(self.password_required_msg)
                if password_sent:
                    raise PasswordError(self.password_incorrect_msg)
                LOG.debug('sending password')
                self.tty_stream.transmit_side.write(
                    mitogen.core.to_text(self.password + '\n').encode('utf-8')
                )
                password_sent = True
        raise mitogen.core.StreamError('bootstrap failed')
