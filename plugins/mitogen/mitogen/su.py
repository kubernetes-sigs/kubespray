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
    # TODO: BSD su cannot handle stdin being a socketpair, but it does let the
    # child inherit fds from the parent. So we can still pass a socketpair in
    # for hybrid_tty_create_child(), there just needs to be either a shell
    # snippet or bootstrap support for fixing things up afterwards.
    create_child = staticmethod(mitogen.parent.tty_create_child)
    child_is_immediate_subprocess = False

    #: Once connected, points to the corresponding DiagLogStream, allowing it to
    #: be disconnected at the same time this stream is being torn down.

    username = 'root'
    password = None
    su_path = 'su'
    password_prompt = b('password:')
    incorrect_prompts = (
        b('su: sorry'),                    # BSD
        b('su: authentication failure'),   # Linux
        b('su: incorrect password'),       # CentOS 6
    )

    def construct(self, username=None, password=None, su_path=None,
                  password_prompt=None, incorrect_prompts=None, **kwargs):
        super(Stream, self).construct(**kwargs)
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if su_path is not None:
            self.su_path = su_path
        if password_prompt is not None:
            self.password_prompt = password_prompt.lower()
        if incorrect_prompts is not None:
            self.incorrect_prompts = map(str.lower, incorrect_prompts)

    def connect(self):
        super(Stream, self).connect()
        self.name = u'su.' + mitogen.core.to_text(self.username)

    def on_disconnect(self, broker):
        super(Stream, self).on_disconnect(broker)

    def get_boot_command(self):
        argv = mitogen.parent.Argv(super(Stream, self).get_boot_command())
        return [self.su_path, self.username, '-c', str(argv)]

    password_incorrect_msg = 'su password is incorrect'
    password_required_msg = 'su password is required'

    def _connect_bootstrap(self, extra_fd):
        password_sent = False
        it = mitogen.parent.iter_read(
            fds=[self.receive_side.fd],
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
                self.transmit_side.write(
                    mitogen.core.to_text(self.password + '\n').encode('utf-8')
                )
                password_sent = True
        raise mitogen.core.StreamError('bootstrap failed')
