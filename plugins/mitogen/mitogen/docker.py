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

    container = None
    image = None
    username = None
    docker_path = 'docker'

    # TODO: better way of capturing errors such as "No such container."
    create_child_args = {
        'merge_stdio': True
    }

    def construct(self, container=None, image=None,
                  docker_path=None, username=None,
                  **kwargs):
        assert container or image
        super(Stream, self).construct(**kwargs)
        if container:
            self.container = container
        if image:
            self.image = image
        if docker_path:
            self.docker_path = docker_path
        if username:
            self.username = username

    def connect(self):
        super(Stream, self).connect()
        self.name = u'docker.' + (self.container or self.image)

    def get_boot_command(self):
        args = ['--interactive']
        if self.username:
            args += ['--user=' + self.username]

        bits = [self.docker_path]
        if self.container:
            bits += ['exec'] + args + [self.container]
        elif self.image:
            bits += ['run'] + args + ['--rm', self.image]

        return bits + super(Stream, self).get_boot_command()
