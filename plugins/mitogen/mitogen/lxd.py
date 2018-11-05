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

import mitogen.core
import mitogen.parent


LOG = logging.getLogger(__name__)


class Stream(mitogen.parent.Stream):
    child_is_immediate_subprocess = False
    create_child_args = {
        # If lxc finds any of stdin, stdout, stderr connected to a TTY, to
        # prevent input injection it creates a proxy pty, forcing all IO to be
        # buffered in <4KiB chunks. So ensure stderr is also routed to the
        # socketpair.
        'merge_stdio': True
    }

    container = None
    lxc_path = 'lxc'
    python_path = 'python'

    eof_error_hint = (
        'Note: many versions of LXC do not report program execution failure '
        'meaningfully. Please check the host logs (/var/log) for more '
        'information.'
    )

    def construct(self, container, lxc_path=None, **kwargs):
        super(Stream, self).construct(**kwargs)
        self.container = container
        if lxc_path:
            self.lxc_path = lxc_path

    def connect(self):
        super(Stream, self).connect()
        self.name = u'lxd.' + self.container

    def get_boot_command(self):
        bits = [
            self.lxc_path,
            'exec',
            '--mode=noninteractive',
            self.container,
            '--',
        ]
        return bits + super(Stream, self).get_boot_command()
